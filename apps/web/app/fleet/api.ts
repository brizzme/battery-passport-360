export async function read<T>(path: string): Promise<T | null> {
  const response = await fetch((process.env.API_BASE_URL ?? "http://127.0.0.1:8000") + path,
    { cache: "no-store", signal: AbortSignal.timeout(6000) });
  if (response.status === 404) return null;
  if (!response.ok) throw Error("Unable to load the requested record.");
  return response.json();
}
export type Battery = {battery_id:string; chemistry:string; category:string; rated_kwh:number; source_id:string; observed_at:string; explanation:string};
export type Evidence = {value_text:string; evidence_ref:string|null; source_id:string; observed_at:string; explanation:string};
export type Result = {rule_id:string;label:string;status:string;reason:string;version:string;section:string;source_url:string;effective_from:string;evidence:Evidence|null};
export type Bench = {vehicle_id:string;assigned_on:string;started_at:string;ended_at:string;energy_kwh:number;sampled_at:string;soc_pct:number;temperature_c:number;serviced_at:string;note:string;source_id:string;observed_at:string;explanation:string};
export type Inspection = {battery:Battery;as_of:string;scenario:string;results:Result[];bench:Bench|null};
export const preset = "2027-02-18";
export const statuses = ["present","missing_evidence","invalid","not_applicable","not_yet_effective","unknown"];
export function dateChoice(value?:string) {
  return value && /^\d{4}-\d\d-\d\d$/.test(value) ? value : "";
}
