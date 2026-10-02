import { NextResponse, type NextRequest } from "next/server";
import { forbidden, forward, sameOrigin, sessionToken } from "@/lib/session";

type Ctx = { params: Promise<{ id: string }> };

// Only a whole number is passed on, so a crafted id cannot reach any other API path.
async function target(ctx: Ctx): Promise<string | null> {
  const { id } = await ctx.params;
  return /^\d{1,10}$/.test(id) ? `/api/v1/portfolios/${id}` : null;
}

async function proxy(req: NextRequest, ctx: Ctx, method: string, write: boolean) {
  if (write && !sameOrigin(req)) return forbidden();
  const token = await sessionToken();
  if (!token) return NextResponse.json({ detail: "Sign in to see your portfolios." }, { status: 401 });
  const path = await target(ctx);
  if (!path) return NextResponse.json({ detail: "Portfolio not found." }, { status: 404 });
  return forward(path, { method, body: write && method !== "DELETE" ? await req.text() : undefined }, token);
}

export const GET = (req: NextRequest, ctx: Ctx) => proxy(req, ctx, "GET", false);
export const PUT = (req: NextRequest, ctx: Ctx) => proxy(req, ctx, "PUT", true);
export const DELETE = (req: NextRequest, ctx: Ctx) => proxy(req, ctx, "DELETE", true);
