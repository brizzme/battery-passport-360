"""Read-only retrieval and constrained optional model selection for synthetic records."""
import json
import re
from datetime import date
from typing import Literal
from urllib.request import Request, urlopen

from fastapi import APIRouter
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings

from .fleet import fleet_cursor, inspect
from .readiness import GAPS

router = APIRouter(prefix="/api", tags=["Local evidence assistant"])


class Question(BaseModel):
    battery_id: str = Field(pattern=r"^BAT-DEMO-\d{3}$")
    as_of: date | None = None
    question: str = Field(min_length=1, max_length=500)


class Passage(BaseModel):
    chunk_id: str
    title: str
    section: str
    version: str
    source_url: str
    access_class: Literal["public"]
    passage: str


COLUMNS = "chunk_id,title,section,version,source_url,access_class,passage"
def citation(rule_id: str) -> str:
    """Each catalogue data point is cited by its indexed guidance row."""
    return "GUID-" + rule_id


@router.get("/reference-sources")
def sources() -> list[Passage]:
    with fleet_cursor() as cursor:
        cursor.execute(f"SELECT {COLUMNS} FROM document_chunks WHERE access_class='public' ORDER BY chunk_id")
        return [Passage(**r) for r in cursor]


def retrieve(terms: str) -> list[Passage]:
    with fleet_cursor() as cursor:
        cursor.execute(f"""SELECT {COLUMNS} FROM document_chunks
            WHERE access_class='public' AND embedding <=> reference_embedding(%s) < 0.94
            ORDER BY embedding <=> reference_embedding(%s), chunk_id LIMIT 3""", (terms, terms))
        return [Passage(**row) for row in cursor]


class Finding(BaseModel):
    field: str
    status: str
    observation: str
    evidence: str | None
    citation_ids: list[str]


class Answer(BaseModel):
    battery_id: str
    as_of: date | None
    mode: str = "offline deterministic retrieval"
    supported: bool = False
    message: str
    findings: list[Finding] = Field(default_factory=list)
    passages: list[Passage] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    next_step: str | None = None


def supported(question: str) -> bool:
    # Deliberately narrow question templates. Free-form input never selects tools.
    clean = " ".join(re.sub(r"bat-demo-\d{3}", "battery", question.lower()).split()).strip(" ?.!")
    return clean in {
        "why is this battery flagged", "why is battery flagged", "what is missing",
        "what should a technician investigate", "show passport evidence",
        "why is battery flagged? what is missing? what should a technician investigate",
    }


class Provider(BaseSettings):
    llm_url: str = ""
    llm_model: str = ""
    llm_api_key: SecretStr = SecretStr("")


def prioritize(answer: Answer, provider: Provider) -> None:
    """Optional chat-completions adapter. Only validated finding IDs can change ordering."""
    if not (provider.llm_url and provider.llm_model and provider.llm_api_key.get_secret_value()):
        return
    ids = [f.field for f in answer.findings]
    payload = {"model":provider.llm_model,"max_tokens":64,"messages":[
        {"role":"system","content":"Return one listed field ID to review first. Prefer missing or invalid evidence."},
        {"role":"user","content":json.dumps([(f.field,f.status) for f in answer.findings])}]}
    req = Request(provider.llm_url, data=json.dumps(payload).encode(), headers={
        "Content-Type":"application/json","Authorization":"Bearer "+provider.llm_api_key.get_secret_value()})
    try:
        with urlopen(req,timeout=6) as response:
            choice = json.loads(response.read(16384))["choices"][0]["message"]["content"].strip()
        if choice not in ids:
            raise ValueError("Unrecognized field")
        answer.findings.sort(key=lambda f: f.field != choice)
        answer.mode = "LLM-assisted ordering of retrieved evidence"
    except (OSError, KeyError, IndexError, ValueError, TypeError, AttributeError):
        answer.mode = "offline deterministic retrieval (provider unavailable or response rejected)"


@router.post("/copilot/query")
def query(request: Question) -> Answer:
    answer = Answer(battery_id=request.battery_id, as_of=request.as_of,
                    message="Supported questions cover missing passport evidence and next evidence checks.")
    named = re.findall(r"BAT-DEMO-\d{3}", request.question.upper())
    if not supported(request.question) or any(name != request.battery_id for name in named):
        return answer
    report = inspect(request.battery_id, request.as_of)
    answer.as_of = report.as_of
    answer.tools = ["get_battery", "check_passport_readiness", "search_reference_documents"]
    gaps = [r for r in report.results if r.status in GAPS]
    unresolved = sum(1 for r in report.results if r.status == "unknown")
    selected = gaps
    hits = retrieve("industrial passport date prospective scope")
    for result in selected:
        hits.extend(retrieve(f"{result.label} data point {result.dp} {result.rule_id} {result.section}"))
    allowed = {"EU-77", *(citation(r.rule_id) for r in selected)}
    passages = list({p.chunk_id: p for p in hits if p.chunk_id in allowed}.values())
    found = {p.chunk_id for p in passages}
    if "EU-77" not in found:
        answer.message = "Insufficient retrieved public reference evidence."
        return answer
    for r in selected:
        ids = [citation(r.rule_id)]
        if not set(ids) <= found:
            answer.message = "Reference coverage is incomplete for this question."
            answer.findings.clear()
            return answer
        evidence = None
        if r.evidence:
            unit = f" {r.evidence.unit}" if r.evidence.unit else ""
            evidence = f"{r.evidence.source_id} · {r.evidence.observed_at.isoformat()} · {r.evidence.value_text}{unit} · {r.evidence.evidence_ref or 'unlinked'}"
        answer.findings.append(Finding(field=r.field,status=r.status,observation=r.reason,
                                       evidence=evidence,citation_ids=["EU-77",*ids]))
    answer.supported = True
    answer.passages = passages
    answer.message = ((f"{len(gaps)} data point(s) have missing or invalid evidence." if gaps else
                       "No missing or invalid evidence for the guidance data points on this date.")
                      + f" {unresolved} data point(s) are unresolved (restricted or design-dependent), not gaps.")
    answer.next_step = ("Request the referenced model sheet and verify the flagged entries and units."
                        if gaps else "Review the applicability dates and retain supporting model sheets.")
    prioritize(answer, Provider())
    return answer
