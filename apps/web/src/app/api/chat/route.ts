import { NextResponse } from "next/server";

// The chat agent is out of scope for this release. Return an explicit error
// instead of a canned reply that looks like an answer.
export async function POST() {
  return NextResponse.json(
    { error: "The research copilot is not available. No answer was generated." },
    { status: 503 },
  );
}
