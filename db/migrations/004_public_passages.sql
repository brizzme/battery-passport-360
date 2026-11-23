BEGIN;
-- Deterministic term-hash embeddings, shared by document ingestion and query.
CREATE OR REPLACE FUNCTION reference_embedding(terms text) RETURNS vector(256)
LANGUAGE sql IMMUTABLE STRICT AS $$
 WITH tokens AS (
   SELECT get_byte(decode(md5(word),'hex'),0) AS bucket
   FROM regexp_split_to_table(lower(terms), '[^a-z0-9]+') word WHERE length(word)>1
 ), counts AS (SELECT bucket,count(*) AS n FROM tokens GROUP BY bucket)
 SELECT array_agg(coalesce(n,0)::real ORDER BY i)::vector(256)
 FROM generate_series(0,255) i LEFT JOIN counts ON bucket=i
$$;
CREATE TABLE IF NOT EXISTS document_chunks (
 chunk_id text PRIMARY KEY, title text NOT NULL, source_url text NOT NULL, section text NOT NULL,
 version text NOT NULL, access_class text NOT NULL, passage text NOT NULL, terms text NOT NULL,
 embedding vector(256) GENERATED ALWAYS AS (reference_embedding(terms || ' ' || passage)) STORED
);
INSERT INTO document_chunks (chunk_id,title,source_url,section,version,access_class,passage,terms)
SELECT id,'Regulation (EU) 2023/1542','https://eur-lex.europa.eu/eli/reg/2023/1542/oj/eng',
 section,'OJ L 191, 28 July 2023','public',passage,terms FROM (VALUES
 ('EU-77','Article 77(1)','From 18 February 2027 each LMT battery, each industrial battery with a capacity greater than 2 kWh and each electric vehicle battery placed on the market or put into service shall have an electronic record (‘battery passport’).','date scope category prospective industrial passport'),
 ('EU-XIII-B','Annex XIII 1(b)','the material composition of the battery, including its chemistry, hazardous substances present in the battery, other than mercury, cadmium or lead, and critical raw materials present in the battery;','chemistry model material'),
 ('EU-XIII-G','Annex XIII 1(g)','rated capacity (in Ah);','rated ah capacity'),
 ('EU-XIII-H','Annex XIII 1(h)','minimal, nominal and maximum voltage, with temperature ranges when relevant;','nominal v voltage'),
 ('EU-XIII-K','Annex XIII 1(k)','capacity threshold for exhaustion (only for electric vehicle batteries);','ev threshold category exhaustion'),
 ('EU-XIII-E','Annex XIII 1(e)','recycled content information as contained in the documentation referred to in Article 8(1);','recycled share materials documentation'),
 ('EU-8','Article 8(1), opening clause','From 18 August 2028 or 24 months after the date of entry into force of the delegated act referred to in the third subparagraph, whichever is the latest,','recycled share date delegated act phased')
) AS ref(id,section,passage,terms) ON CONFLICT DO NOTHING;
INSERT INTO schema_migrations(version) VALUES ('004_public_passages') ON CONFLICT DO NOTHING;
COMMIT;
