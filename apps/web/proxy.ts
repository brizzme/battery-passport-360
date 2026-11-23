import {NextResponse, type NextRequest} from "next/server";
import {authorised} from "./lib/basicAuth";

/**
 * Optional sign-in for a shared demo link. Active only when DEMO_USER and DEMO_PASSWORD are set
 * (server-side environment, read at request time); local development stays open.
 */
export function proxy(request: NextRequest) {
  const user = process.env.DEMO_USER, password = process.env.DEMO_PASSWORD;
  if (!user || !password) return NextResponse.next();
  if (authorised(request.headers.get("authorization"), user, password)) return NextResponse.next();
  return new NextResponse("Sign-in required", {
    status: 401,
    headers: {"WWW-Authenticate": 'Basic realm="Battery Passport 360 demo", charset="UTF-8"', "Cache-Control": "no-store"},
  });
}

// Everything except the health endpoint used by the hosting platform's health check.
export const config = {matcher: ["/((?!health$|robots\\.txt$).*)"]};
