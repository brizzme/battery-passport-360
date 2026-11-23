# Local architecture

The Next.js App Router serves the workspace on port 3000. Its server fetches FastAPI on the private Compose network for each page request. The page reports a connection failure if the health check times out or fails. The browser can also open the API reference directly via the loopback port.

FastAPI exposes its Pydantic health response at GET /health. The endpoint returns HTTP 200 when a PostgreSQL connection succeeds and the vector extension exists, or HTTP 503 otherwise. GET /openapi.json describes the contract.

Compose starts PostgreSQL 16 with a named volume, waits for readiness, and runs the numbered SQL files in lexical order with psql configured to stop on error. Each migration must be transactional and safe to replay. The foundation migration enables pgvector and records its version. The API starts after successful migration and the web service starts after API readiness. Only the API and web ports are published, on loopback.

Python dependencies resolve through uv.lock and frontend dependencies through package-lock.json. Fonts are packaged with the web application.

Migration 002 creates the first two fleet tables and seeds fictional identities. GET /api/batteries/{battery_id} joins the identity to its source and returns HTTP 404 for an unknown ID. This first M1 slice is available through the API reference.

The inspector reads the simulated bench tables and linked model-sheet fields, then evaluates five versioned Python rules. The fleet status filter uses the same evaluator as the inspector. Reports and offline assistant findings therefore use the same date, scope checks, field values and evidence references.

The CALCE pipeline runs outside the server and emits an aggregate model artifact plus ignored local observation files. The research router has its own cell namespace with no pack identifier mapping. Empty local research storage leaves the aggregate report available.

The reference index stores seven public excerpts in PostgreSQL with section, version, access class and 256-dimensional term-hash vectors. Read-only queries rank candidates by cosine distance and check for the expected section before citing it. The corpus is small, so exact vector search is sufficient. This is lexical retrieval with curated field terms. The assistant accepts bounded investigation questions, uses fixed read-only functions, and returns a trace of its lookup operations. Retrieved text is data. The optional provider can reorder known fields only. The Markdown draft is generated on demand from the same inspector response.
