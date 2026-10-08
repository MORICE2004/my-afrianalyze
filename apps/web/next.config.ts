import type { NextConfig } from "next";

// A production build without a real API address would ship a site whose every data request goes to the
// visitor's own machine (the localhost default in src/lib/api.ts). Fail the build instead. Preview builds
// may still build without it; their pages then say the API is not reachable. VERCEL_ENV is set by Vercel.
if (process.env.VERCEL_ENV === "production") {
  const url = process.env.NEXT_PUBLIC_API_URL ?? "";
  if (!url.startsWith("https://")) {
    throw new Error("NEXT_PUBLIC_API_URL must be set to the API's https:// address for a production build.");
  }
}

const isDev = process.env.NODE_ENV !== "production";
const apiOrigin = (() => {
  try {
    return new URL(process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").origin;
  } catch {
    return "";
  }
})();

// Content-Security-Policy. The browser may talk only to this site and the AfriEdge API, may not be framed,
// and may not load plugins or post forms elsewhere. Scripts allow 'unsafe-inline' because Next.js injects
// inline scripts; a nonce-based policy would make every page render per request, and is a later step
// (docs/SECURITY_MODEL.md). Dev also needs eval and websockets for hot reload.
const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  // Add a news publisher's image host here only when config/news_sources.json marks its images PERMITTED.
  "img-src 'self' data: blob:",
  "font-src 'self' data:",
  `connect-src 'self' ${apiOrigin}${isDev ? " ws: wss:" : ""}`.trim(),
  "frame-src 'none'",
  "frame-ancestors 'none'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const nextConfig: NextConfig = {
  // The development-only build indicator (never in production builds) sits where it covers no page content.
  devIndicators: { position: "bottom-right" },
  // Self-contained server bundle for the Docker image (apps/web/Dockerfile copies .next/standalone).
  // Vercel builds and runs the app its own way and does not want a standalone bundle, so leave it off
  // there. VERCEL is set by Vercel itself during the build.
  output: process.env.VERCEL ? undefined : "standalone",
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: csp },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },
};

export default nextConfig;
