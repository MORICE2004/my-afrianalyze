import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Self-contained server bundle for the Docker image (apps/web/Dockerfile copies .next/standalone).
  // Vercel builds and runs the app its own way and does not want a standalone bundle, so leave it off
  // there. VERCEL is set by Vercel itself during the build.
  output: process.env.VERCEL ? undefined : "standalone",
};

export default nextConfig;
