"use client";
import Link from "next/link";
export default function ErrorView({reset}:{reset:()=>void}) {
  return <main><h1>Couldn’t load records</h1><p>Check your date and the local API connection.</p><button onClick={reset}>Retry</button> <Link href="/fleet">Reset filters</Link></main>
}
