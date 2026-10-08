// Server-side only (imported by route handlers under src/app/api/). Holds the sign-in token in an httpOnly
// cookie on the web app's own domain and forwards it to the API as a Bearer token. Browser JavaScript
// never sees the token, and the browser never calls the API's signed-in endpoints directly.
import { cookies, headers } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

export const SESSION_COOKIE = "afriedge_session";
const API = (process.env.API_URL_INTERNAL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

// Cross-site request forgery guard for anything that changes state: the request must come from a page on
// this same site. The cookie is SameSite=Lax as well; this is the second lock.
export function sameOrigin(req: NextRequest): boolean {
  const origin = req.headers.get("origin");
  const host = req.headers.get("x-forwarded-host") ?? req.headers.get("host");
  if (!origin || !host) return false;
  try {
    return new URL(origin).host === host;
  } catch {
    return false;
  }
}

export function forbidden(): NextResponse {
  return NextResponse.json({ detail: "This request must come from the AfriEdge site itself." }, { status: 403 });
}

export async function sessionToken(): Promise<string | undefined> {
  return (await cookies()).get(SESSION_COOKIE)?.value;
}

export async function setSession(token: string, expiresAt: string): Promise<void> {
  (await cookies()).set(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    expires: new Date(expiresAt),
  });
}

export async function clearSession(): Promise<void> {
  (await cookies()).delete(SESSION_COOKIE);
}

// Calls the API and passes its status and body straight back, so the page sees the API's own messages.
// The visitor's address, as the hosting platform reports it. Vercel sets x-real-ip and the right of
// x-forwarded-for itself; a visitor cannot change those values on Vercel.
async function visitorIp(): Promise<string | null> {
  const h = await headers();
  const xff = h.get("x-forwarded-for");
  return h.get("x-real-ip") ?? (xff ? xff.split(",").pop()!.trim() : null);
}

// The visitor's cookie choice (components/CookieConsent.tsx), read on this server for requests it forwards.
export async function analyticsConsent(): Promise<boolean> {
  const raw = (await cookies()).get("afriedge_consent")?.value;
  try {
    return raw ? JSON.parse(decodeURIComponent(raw)).analytics === true : false;
  } catch {
    return false;
  }
}

export async function forward(path: string, init: RequestInit = {}, token?: string): Promise<NextResponse> {
  const headers = new Headers(init.headers);
  if (init.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (await analyticsConsent()) headers.set("X-Analytics-Consent", "granted");
  // Requests reach the API from this server, so tell the API who the visitor is, with the shared secret that
  // proves the header came from here (without it the API would rate-limit every visitor as one).
  const secret = process.env.INTERNAL_PROXY_SECRET;
  const ip = await visitorIp();
  if (secret && ip) {
    headers.set("x-afriedge-client-ip", ip);
    headers.set("x-afriedge-proxy-key", secret);
  }
  try {
    const res = await fetch(`${API}${path}`, { ...init, headers, cache: "no-store" });
    if (res.status === 204) return new NextResponse(null, { status: 204 });
    const body = await res.json().catch(() => ({ detail: `Request failed (${res.status})` }));
    return NextResponse.json(body, { status: res.status });
  } catch {
    return NextResponse.json({ detail: "The data service is not reachable. Nothing was saved." }, { status: 503 });
  }
}
