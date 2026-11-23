"use client";
import Link from "next/link";
import {usePathname} from "next/navigation";

const ICONS: Record<string, React.ReactNode> = {
  summary: <path d="M5 3h7l4 4v10H5zM12 3v4h4M8 10h5M8 13h5"/>,
  health: <path d="M2 11h4l2-5 3 9 2-4h5"/>,
  passport: <><rect x="3" y="4" width="14" height="12" rx="1"/><circle cx="8" cy="9" r="2"/><path d="M5.5 13.5c.6-1.2 1.5-1.8 2.5-1.8s1.9.6 2.5 1.8M12 8h3M12 11h3"/></>,
  research: <path d="M8 3v5L4 15.5c-.4.8.2 1.5 1 1.5h10c.8 0 1.4-.7 1-1.5L12 8V3M7 3h6M6 12h8"/>,
  assistant: <path d="M4 4h12v9H9l-4 3v-3H4z"/>,
};
const Icon = ({name}: {name: string}) => <svg className="nav-icon" width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{ICONS[name]}</svg>;

const NAV = [
  {href: "/", icon: "summary", label: "PoC summary", match: (p: string) => p === "/"},
  {href: "/fleet-health", icon: "health", label: "Fleet health", match: (p: string) => p.startsWith("/fleet-health")},
  {href: "/fleet", icon: "passport", label: "Passport inspector", match: (p: string) => p === "/fleet" || p.startsWith("/fleet/")},
  {href: "/research", icon: "research", label: "Cell research", match: (p: string) => p.startsWith("/research")},
  {href: "/assistant?id=BAT-DEMO-024&as_of=2027-02-18", icon: "assistant", label: "Evidence assistant", match: (p: string) => p.startsWith("/assistant")},
];

export function Shell({children}: {children: React.ReactNode}) {
  const path = usePathname() ?? "/";
  return <div className="app">
    <a className="skip" href="#main">Skip to content</a>
    <header className="bar">
      <Link href="/" className="wordmark"><svg width="22" height="14" viewBox="0 0 22 14" aria-hidden="true"><rect x="1" y="1" width="17" height="12" fill="none" stroke="currentColor" strokeWidth="2"/><rect x="19" y="4.5" width="2.5" height="5" fill="currentColor"/><rect x="4" y="4" width="7" height="6" fill="currentColor"/></svg>Battery Passport 360</Link>
      <nav aria-label="Main"><ul>{NAV.map(n => <li key={n.href}><Link href={n.href} aria-current={n.match(path) ? "page" : undefined}><Icon name={n.icon}/>{n.label}</Link></li>)}</ul></nav>
      <p className="synthetic-label">Synthetic fleet · calibrated · data cut-off 31 Oct 2026</p>
    </header>
    <div className="app-main">
    <main id="main" tabIndex={-1}>{children}</main>
    <footer className="foot">
      <p>Battery Passport 360 is an independent prototype. Fleet data is fictional and simulated; it does not describe real batteries, customers or certifications.</p>
      <p><a href="/docs">API reference</a> · <a href="/health">Service health (JSON)</a></p>
    </footer>
    </div>
  </div>;
}
