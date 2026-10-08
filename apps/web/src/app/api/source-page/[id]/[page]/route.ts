import { NextResponse } from "next/server";
import { sessionToken } from "@/lib/session";

const API = (process.env.API_URL_INTERNAL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

// One rendered page of a source document. The session token lives in an httpOnly cookie here, so the browser asks
// this route and it forwards the token; the API decides. Only a PNG ever passes through, never the PDF.
export async function GET(req: Request, ctx: RouteContext<"/api/source-page/[id]/[page]">) {
  const { id, page } = await ctx.params;
  if (!/^\d{1,9}$/.test(id) || !/^\d{1,5}$/.test(page)) return NextResponse.json({ detail: "Not found." }, { status: 404 });
  const token = await sessionToken();
  if (!token) return NextResponse.json({ detail: "Sign in to view source documents." }, { status: 401 });
  const headers = new Headers({ Authorization: `Bearer ${token}` });
  const secret = process.env.INTERNAL_PROXY_SECRET;
  const ip = req.headers.get("x-real-ip");
  if (secret && ip) {
    headers.set("x-afriedge-client-ip", ip);
    headers.set("x-afriedge-proxy-key", secret);
  }
  try {
    const res = await fetch(`${API}/api/v1/sources/${id}/pages/${page}`, { headers, cache: "no-store" });
    if (!res.ok || res.headers.get("content-type") !== "image/png") {
      return NextResponse.json({ detail: "Page not available." }, { status: res.ok ? 502 : res.status });
    }
    return new NextResponse(res.body, {
      status: 200,
      headers: { "Content-Type": "image/png", "Cache-Control": "private, no-store", "Content-Disposition": "inline", "X-Content-Type-Options": "nosniff" },
    });
  } catch {
    return NextResponse.json({ detail: "The data service is not reachable." }, { status: 503 });
  }
}
