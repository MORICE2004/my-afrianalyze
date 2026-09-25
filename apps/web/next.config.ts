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

const nextConfig: NextConfig = {
  // Self-contained server bundle for the Docker image (apps/web/Dockerfile copies .next/standalone).
  // Vercel builds and runs the app its own way and does not want a standalone bundle, so leave it off
  // there. VERCEL is set by Vercel itself during the build.
  output: process.env.VERCEL ? undefined : "standalone",
};

export default nextConfig;
