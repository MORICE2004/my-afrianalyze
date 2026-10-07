import { NextResponse, type NextRequest } from "next/server";
import { forbidden, forward, sameOrigin, sessionToken } from "@/lib/session";

// The copilot costs money per question, so it needs a signed-in user (the API also caps questions per day).
export async function POST(req: NextRequest) {
  if (!sameOrigin(req)) return forbidden();
  const token = await sessionToken();
  if (!token) return NextResponse.json({ detail: "Sign in to ask the research copilot." }, { status: 401 });
  return forward("/api/v1/copilot/ask", { method: "POST", body: await req.text() }, token);
}
