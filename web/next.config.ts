import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Los datos de cada periodo se leen del disco en build (data/periodos/*.json).
  outputFileTracingIncludes: { "/**": ["./data/periodos/**"] },
};

export default nextConfig;
