import { NextResponse } from "next/server";
import { forward, sessionToken } from "@/lib/session";

// Administrators only: the API checks the role on every request; this only forwards the session.
export async function GET() {
  const token = await sessionToken();
  if (!token) return NextResponse.json({ detail: "Sign in to continue." }, { status: 401 });
  return forward("/api/v1/admin/data-health", {}, token);
}
