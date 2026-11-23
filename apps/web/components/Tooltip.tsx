"use client";
import {useEffect, useState} from "react";

/** One tooltip for every element carrying data-tip; follows hover and keyboard focus. */
export function Tooltip() {
  const [tip, setTip] = useState<{text: string; x: number; y: number} | null>(null);
  useEffect(() => {
    const show = (e: Event) => {
      const el = (e.target as Element | null)?.closest?.("[data-tip]");
      if (!el) return;
      const r = el.getBoundingClientRect();
      setTip({text: el.getAttribute("data-tip") ?? "", x: r.left + r.width / 2, y: r.top});
    };
    const hide = (e: Event) => { if ((e.target as Element | null)?.closest?.("[data-tip]")) setTip(null); };
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") setTip(null); };
    document.addEventListener("pointerover", show); document.addEventListener("focusin", show);
    document.addEventListener("pointerout", hide); document.addEventListener("focusout", hide);
    document.addEventListener("keydown", esc); window.addEventListener("scroll", () => setTip(null), {passive: true});
    return () => {
      document.removeEventListener("pointerover", show); document.removeEventListener("focusin", show);
      document.removeEventListener("pointerout", hide); document.removeEventListener("focusout", hide);
      document.removeEventListener("keydown", esc);
    };
  }, []);
  if (!tip) return null;
  return <div role="tooltip" className="tip" style={{left: tip.x, top: tip.y}}>{tip.text}</div>;
}
