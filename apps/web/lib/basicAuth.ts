import {createHash, timingSafeEqual} from "node:crypto";

const digest = (s: string) => createHash("sha256").update(s).digest();

/** True when the Authorization header carries exactly user:password (constant-time comparison). */
export function authorised(header: string | null, user: string, password: string): boolean {
  if (!header?.startsWith("Basic ")) return false;
  let decoded: string;
  try { decoded = Buffer.from(header.slice(6), "base64").toString("utf8"); } catch { return false; }
  return timingSafeEqual(digest(decoded), digest(`${user}:${password}`));
}
