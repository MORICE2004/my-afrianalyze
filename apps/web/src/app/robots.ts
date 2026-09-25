import type { MetadataRoute } from "next";

// Search engines stay out until the owner turns indexing on deliberately (NEXT_PUBLIC_ALLOW_INDEXING=true),
// which should wait until reports have been reviewed and published. Unpublished drafts must not be indexed.
export default function robots(): MetadataRoute.Robots {
  if (process.env.NEXT_PUBLIC_ALLOW_INDEXING === "true") {
    return { rules: { userAgent: "*", allow: "/" } };
  }
  return { rules: { userAgent: "*", disallow: "/" } };
}
