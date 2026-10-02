import { NextResponse, type NextRequest } from "next/server";
import { clearSession, forbidden, forward, sameOrigin, sessionToken } from "@/lib/session";

export async function POST(req: NextRequest) {
  if (!sameOrigin(req)) return forbidden();
  const token = await sessionToken();
  if (token) await forward("/api/v1/auth/logout", { method: "POST" }, token);   // revoke it on the API too
  await clearSession();
  return new NextResponse(null, { status: 204 });
}
