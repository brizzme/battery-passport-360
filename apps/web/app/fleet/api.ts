export async function read<T>(path: string): Promise<T | null> {
  const response = await fetch((process.env.API_BASE_URL ?? "http://127.0.0.1:8000") + path,
    { cache: "no-store", signal: AbortSignal.timeout(6000) });
  if (response.status === 404) return null;
  if (!response.ok) throw Error("Unable to load the requested record.");
  return response.json();
}
export type Battery = {battery_id:string; chemistry:string; category:string; rated_kwh:number; source_id:string; observed_at:string; explanation:string};
export type Evidence = {value_text:string; unit:string|null; evidence_ref:string|null; source_id:string; observed_at:string; explanation:string};
export type Result = {rule_id:string;dp:number;label:string;status:string;reason:string;version:string;section:string;guidance_ref:string;access:string;source_url:string;eurlex_url:string;effective_from:string|null;evidence:Evidence|null};
export type Indicator = {key:string;label:string;value:number|string|null;unit:string|null;status:string;reason:string|null;passport_field:boolean;passport_ref:string|null;access_class:string;mapping_status:string|null;calibration_refs:string[];labels:string[]};
export type Health = {battery_id:string;as_of:string;data_cutoff:string;source_type:"synthetic";source_id:string;generator_version:string;calibration_version:string;site_id:string|null;chemistry:string;indicators:Indicator[];not_applicable:Indicator[];events:{observed_at:string;kind:string;detail:string}[];temperature_histogram:Bin[];soc_histogram:Bin[]};
export type Bin = {bin_lower:number;bin_upper:number;hours:number};
export type Inspection = {battery:Battery;as_of:string;scenario:string;results:Result[];health:Health|null;coverage:Record<string,number>};
export const preset = "2027-02-18";
export const statuses = ["present","missing_evidence","invalid","not_applicable","not_yet_effective","unknown"];
export function dateChoice(value?:string) {
  return value && /^\d{4}-\d\d-\d\d$/.test(value) ? value : "";
}
