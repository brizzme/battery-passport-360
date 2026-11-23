import json
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app import copilot


def answer():
    passages = [copilot.Passage(chunk_id=i, title="t", section="s", version="v", access_class="public",
                                source_url="https://example.org", passage=i) for i in ("EU-77", "GUID-DP-11", "GUID-DP-12")]
    findings = [copilot.Finding(field=f, status=s, observation="o", evidence=None, citation_ids=["EU-77", "GUID-" + f])
                for f, s in (("DP-11", "invalid"), ("DP-12", "missing_evidence"))]
    return copilot.Answer(battery_id="BAT-DEMO-024", as_of=None, supported=True, message="m",
                          findings=findings, passages=passages)


class FakeClient:
    def __init__(self, payload=None, stop="end_turn", error=None):
        self.payload, self.stop, self.error, self.calls = payload, stop, error, []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def create(self, **kw):
        self.calls.append(kw)
        if self.error:
            raise self.error
        return SimpleNamespace(stop_reason=self.stop, model=kw["model"],
                               content=[SimpleNamespace(type="text", text=json.dumps(self.payload))])


GOOD = {"summary": "Two passport entries need a specialist check before placement.",
        "priorities": [{"field": "DP-12", "why": "Chemistry has no model-sheet reference.", "citation_ids": ["GUID-DP-12"]},
                       {"field": "DP-11", "why": "Capacity entry is not a number in Ah.", "citation_ids": ["GUID-DP-11", "EU-77"]}]}
CFG = copilot.Provider(anthropic_api_key=SecretStr("test-key"))


def test_no_key_keeps_offline_mode():
    a = answer()
    copilot.explain(a, copilot.Provider(anthropic_api_key=SecretStr("")))
    assert a.mode == "offline deterministic retrieval" and a.explanation is None


def test_valid_explanation_is_attached_and_reorders_findings():
    a, client = answer(), FakeClient(GOOD)
    copilot.explain(a, CFG, client=client)
    assert a.explanation.summary.startswith("Two passport entries")
    assert [f.field for f in a.findings] == ["DP-12", "DP-11"]
    assert a.mode == "LLM-assisted explanation (claude-sonnet-5-5) over offline retrieval"
    sent = client.calls[0]
    assert sent["model"] == "claude-sonnet-5-5" and sent["fallbacks"] == "default"
    assert "BAT-DEMO-024" in json.dumps(sent["messages"]) and sent["output_config"]["format"]["type"] == "json_schema"


@pytest.mark.parametrize("bad", [
    {**GOOD, "priorities": [{"field": "DP-99", "why": "x", "citation_ids": ["GUID-DP-11"]}]},
    {**GOOD, "priorities": [{"field": "DP-11", "why": "x", "citation_ids": ["EU-999"]}]},
    {"summary": "compliant", "priorities": []},
])
def test_invalid_or_certifying_output_rejected(bad):
    a = answer()
    copilot.explain(a, CFG, client=FakeClient(bad))
    assert a.explanation is None and "rejected" in a.mode


def test_refusal_falls_back_offline():
    a = answer()
    copilot.explain(a, CFG, client=FakeClient(GOOD, stop="refusal"))
    assert a.explanation is None and "rejected" in a.mode


def test_api_error_falls_back_offline():
    import anthropic
    a = answer()
    copilot.explain(a, CFG, client=FakeClient(error=anthropic.APIConnectionError(request=None)))
    assert a.explanation is None and "unavailable" in a.mode


def test_unsupported_answer_never_calls_claude():
    a, client = answer(), FakeClient(GOOD)
    a.supported = False
    copilot.explain(a, CFG, client=client)
    assert client.calls == []


def test_rate_limit_falls_back_visibly(monkeypatch):
    from app import copilot
    monkeypatch.setattr(copilot, "_calls", copilot.deque())
    assert copilot._allow_call(2, now=0) and copilot._allow_call(2, now=1)
    assert not copilot._allow_call(2, now=2)
    assert copilot._allow_call(2, now=61)
