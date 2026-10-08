import { NextResponse } from "next/server";
import { sessionToken } from "@/lib/session";

const API = (process.env.API_URL_INTERNAL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

// Pro exports: the workbook (default) or the PDF report (?format=pdf). The browser cannot send the session to the API itself (the token lives in an httpOnly cookie
// here), so this forwards the request with the token and passes the file through. The API decides who may have it.
export async function GET(_req: Request, ctx: RouteContext<"/api/export/[symbol]">) {
  const { symbol } = await ctx.params;
  const id = decodeURIComponent(symbol).toUpperCase();
  if (!/^[A-Z]{2,5}:[A-Z0-9.]{1,12}$/.test(id)) {
    return NextResponse.json({ detail: "Unrecognised ticker." }, { status: 400 });
  }
  const token = await sessionToken();
  if (!token) return NextResponse.json({ detail: "Sign in to export." }, { status: 401 });
  const headers = new Headers({ Authorization: `Bearer ${token}` });
  const secret = process.env.INTERNAL_PROXY_SECRET;
  const ip = _req.headers.get("x-real-ip");
  if (secret && ip) {
    headers.set("x-afriedge-client-ip", ip);
    headers.set("x-afriedge-proxy-key", secret);
  }
  try {
    const format = new URL(_req.url).searchParams.get("format") === "pdf" ? "pdf" : "xlsx";
    const res = await fetch(`${API}/api/v1/reports/${encodeURIComponent(id)}/${format}`, { headers, cache: "no-store" });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: `Export failed (${res.status})` }));
      return NextResponse.json(body, { status: res.status });
    }
    return new NextResponse(res.body, {
      status: 200,
      headers: {
        "Content-Type": res.headers.get("content-type") ?? "application/octet-stream",
        "Content-Disposition": res.headers.get("content-disposition") ?? `attachment; filename="AfriEdge.xlsx"`,
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return NextResponse.json({ detail: "The data service is not reachable." }, { status: 503 });
  }
}
