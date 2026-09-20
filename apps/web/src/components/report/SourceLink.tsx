import React from "react";
import { sourceFileUrl, type DocRef } from "@/lib/api";

// Wraps a displayed figure so that clicking it opens the source document at the cited page.
export function SourceLink({
  source,
  children,
  method,
}: {
  source: DocRef;
  children: React.ReactNode;
  method?: string;
}) {
  const title = `${source.title}, page ${source.page ?? "n/a"}${method ? ` (extracted by ${method})` : ""}`;
  // Exchange price data is not served on, so those sources carry no file. Link to the address it came from.
  const href = source.file_url ? sourceFileUrl(source.file_url) : source.url;
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      title={title}
      data-source-page={source.page ?? ""}
      className="underline decoration-neutral-300 decoration-dotted underline-offset-4 hover:decoration-black"
    >
      {children}
    </a>
  );
}

export function ExternalSource({ href, children }: { href: string; children: React.ReactNode }) {
  const url = href.split(" ")[0];
  return (
    <a href={url} target="_blank" rel="noopener noreferrer" className="underline underline-offset-4 break-all">
      {children}
    </a>
  );
}
