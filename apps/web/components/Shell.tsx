"use client";
import Link from "next/link";
import {usePathname} from "next/navigation";

const NAV = [
  {href: "/", label: "PoC summary", match: (p: string) => p === "/"},
  {href: "/fleet-health", label: "Fleet health", match: (p: string) => p.startsWith("/fleet-health")},
  {href: "/fleet", label: "Passport inspector", match: (p: string) => p === "/fleet" || p.startsWith("/fleet/")},
  {href: "/research", label: "Cell research", match: (p: string) => p.startsWith("/research")},
  {href: "/assistant?id=BAT-DEMO-024&as_of=2027-02-18", label: "Evidence assistant", match: (p: string) => p.startsWith("/assistant")},
];

export function Shell({children}: {children: React.ReactNode}) {
  const path = usePathname() ?? "/";
  return <>
    <a className="skip" href="#main">Skip to content</a>
    <header className="bar">
      <Link href="/" className="wordmark"><svg width="22" height="14" viewBox="0 0 22 14" aria-hidden="true"><rect x="1" y="1" width="17" height="12" fill="none" stroke="currentColor" strokeWidth="2"/><rect x="19" y="4.5" width="2.5" height="5" fill="currentColor"/><rect x="4" y="4" width="7" height="6" fill="currentColor"/></svg>Battery Passport 360</Link>
      <nav aria-label="Main"><ul>{NAV.map(n => <li key={n.href}><Link href={n.href} aria-current={n.match(path) ? "page" : undefined}>{n.label}</Link></li>)}</ul></nav>
      <p className="synthetic-label">Synthetic fleet · calibrated · data cut-off 31 Oct 2026</p>
    </header>
    <main id="main" tabIndex={-1}>{children}</main>
    <footer className="foot">
      <p>Battery Passport 360 is an independent prototype. Fleet data is fictional and simulated; it does not describe real batteries, customers or certifications.</p>
      <p><a href="/docs">API reference</a> · <a href="/health">Service health (JSON)</a></p>
    </footer>
  </>;
}
