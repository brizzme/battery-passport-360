/** SVG hatch pattern shared by charts: extrapolated, clamped or unknown values. */
export function HatchDefs({id = "hatch"}: {id?: string}) {
  return <defs><pattern id={id} width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="6" height="6" fill="transparent"/><line x1="0" y1="0" x2="0" y2="6" stroke="#1d2b33" strokeOpacity=".4" strokeWidth="1.5"/>
  </pattern></defs>;
}
