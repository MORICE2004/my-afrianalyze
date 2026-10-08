"use client";

import React, { useState } from "react";
import type { LibraryPhoto as Photo } from "@/lib/api";

// An openly licensed photograph from AfriEdge's library (Wikimedia Commons), served from this site. The caption
// says what the photo shows and the credit names the author and licence, as the licence requires. If the file
// fails to load, nothing broken is shown: the fallback renders instead.
export function LibraryPhoto({ photo, ratio = "aspect-[16/9]", large = false, fallback, eager = false }: {
  photo: Photo; ratio?: string; large?: boolean; fallback?: React.ReactNode; eager?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  if (failed) return <>{fallback ?? null}</>;
  return (
    <figure className={`relative overflow-hidden rounded-md bg-surface-2 ${ratio}`} data-testid="library-photo">
      {/* eslint-disable-next-line @next/next/no-img-element -- a fixed local file with known dimensions */}
      <img src={photo.url} alt={photo.caption} width={photo.width} height={photo.height} loading={eager ? "eager" : "lazy"} decoding="async"
        onError={() => setFailed(true)} className="absolute inset-0 h-full w-full object-cover" />
      <figcaption className={`absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent text-white ${large ? "px-4 pb-3 pt-10" : "px-2.5 pb-2 pt-6"}`}>
        <span className={`block font-medium ${large ? "text-xs" : "text-[10px]"}`}>{photo.caption}</span>
        <span className="block text-[10px] text-white/75">
          Photo: {photo.author},{" "}
          <a href={photo.source_page} target="_blank" rel="noopener noreferrer" className="relative z-10 underline underline-offset-2">{photo.licence}</a>
        </span>
      </figcaption>
    </figure>
  );
}
