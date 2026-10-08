"use client";

import React from "react";

export function CookiePreferencesButton() {
  return (
    <button type="button" onClick={() => window.dispatchEvent(new Event("afriedge:cookie-preferences"))}
      className="mt-3 inline-flex h-9 items-center rounded-md border border-line-strong px-3.5 text-sm font-medium hover:bg-surface-2">
      Cookie preferences
    </button>
  );
}
