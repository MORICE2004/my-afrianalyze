import { NextResponse, type NextRequest } from "next/server";
import { forbidden, forward, sameOrigin, setSession } from "@/lib/session";

// Shared by login and signup: ask the API, keep the token in the httpOnly cookie, and give the page only
// the user's id and email. The token never appears in a response the page's JavaScript can read.
export async function signIn(req: NextRequest, apiPath: string): Promise<NextResponse> {
  if (!sameOrigin(req)) return forbidden();
  const payload = await req.json().catch(() => null);
  const res = await forward(apiPath, { method: "POST", body: JSON.stringify(payload ?? {}) });
  if (!res.ok) return res;
  const body = await res.json();
  await setSession(body.token, body.expires_at);
  return NextResponse.json({ user: body.user }, { status: res.status });
}
