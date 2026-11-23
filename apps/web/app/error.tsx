"use client";
export default function DashboardError({reset}: {reset: () => void}) {
  return <div className="page-head state"><h1>Fleet health is unavailable</h1>
    <p>The local API did not answer. Check that the stack is running (<code>docker compose ps</code>), then retry.</p>
    <p><button onClick={reset}>Retry</button></p></div>;
}
