export function ProvenancePanel({calibration, generator, cutoff}: {calibration: string; generator: string; cutoff: string}) {
  return <section aria-labelledby="prov-h" className="provenance">
    <h2 id="prov-h">Where these numbers come from</h2>
    <dl>
      <div><dt>Fleet</dt><dd>100 fictional packs, daily history to {cutoff}, generator {generator}. Synthetic: no real batteries or customers.</dd></div>
      <div><dt>Fade spread and curve shape</dt><dd>HUST LFP cells, 77 measured to 80 % capacity (Ma et al. 2022, CC BY 4.0).</dd></div>
      <div><dt>Fade per cycle, temperature, resistance</dt><dd>Aalborg forklift-profile LFP cells, 3 at 35/40/45 °C (Vilsen &amp; Stroe 2024, CC BY 4.0).</dd></div>
      <div><dt>Calibration</dt><dd>{calibration}. Cell measurements applied to fictional packs; no validated cell-to-pack model.</dd></div>
    </dl>
  </section>;
}
