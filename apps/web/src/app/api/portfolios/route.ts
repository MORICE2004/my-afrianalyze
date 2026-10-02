import { NextResponse, type NextRequest } from "next/server";
import { forbidden, forward, sameOrigin, sessionToken } from "@/lib/session";

const NOT_SIGNED_IN = { detail: "Sign in to see your portfolios." };

export async function GET() {
  const token = await sessionToken();
  if (!token) return NextResponse.json(NOT_SIGNED_IN, { status: 401 });
  return forward("/api/v1/portfolios", {}, token);
}

export async function POST(req: NextRequest) {
  if (!sameOrigin(req)) return forbidden();
  const token = await sessionToken();
  if (!token) return NextResponse.json(NOT_SIGNED_IN, { status: 401 });
  return forward("/api/v1/portfolios", { method: "POST", body: await req.text() }, token);
}
