import { NextResponse, type NextRequest } from "next/server";
import { forward, sessionToken } from "@/lib/session";

type Ctx = { params: Promise<{ id: string }> };

export async function GET(_req: NextRequest, ctx: Ctx) {
  const token = await sessionToken();
  if (!token) return NextResponse.json({ detail: "Sign in to see your portfolios." }, { status: 401 });
  const { id } = await ctx.params;
  if (!/^\d{1,10}$/.test(id)) return NextResponse.json({ detail: "Portfolio not found." }, { status: 404 });
  return forward(`/api/v1/portfolios/${id}/analysis`, {}, token);
}
