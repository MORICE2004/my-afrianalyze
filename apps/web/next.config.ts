import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Self-contained server bundle for the Docker image (apps/web/Dockerfile copies .next/standalone).
  output: "standalone",
};

export default nextConfig;
