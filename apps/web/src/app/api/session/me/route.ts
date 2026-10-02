import { NextResponse } from "next/server";
import { clearSession, forward, sessionToken } from "@/lib/session";

// Being signed out is a normal state, not an error, so this answers 200 with user: null instead of 401
// (a 401 would show as a red error in every signed-out visitor's console). A session the API no longer
// accepts (expired or revoked) is cleared here.
export async function GET() {
  const token = await sessionToken();
  if (!token) return NextResponse.json({ user: null });
  const res = await forward("/api/v1/auth/me", {}, token);
  if (res.status === 401) {
    await clearSession();
    return NextResponse.json({ user: null });
  }
  if (!res.ok) return res;
  return NextResponse.json({ user: await res.json() });
}
