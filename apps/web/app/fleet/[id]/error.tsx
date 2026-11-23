"use client";
import Link from "next/link";
export default function PackError({reset}: {reset: () => void}) {
  return <div className="page-head state"><h1>This pack could not be loaded</h1>
    <p>The local API did not answer for this pack. Check that the stack is running (<code>docker compose ps</code>), then retry.</p>
    <p><button onClick={reset}>Retry</button> <Link href="/fleet">Back to the passport inspector</Link></p></div>;
}
