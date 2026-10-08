import React from "react";

// Shared layout for the quiet information pages linked from the footer.
export function InfoPage({ title, lead, children, testId }: { title: string; lead: string; children: React.ReactNode; testId?: string }) {
  return (
    <article className="mx-auto max-w-2xl pb-12 text-[15px] leading-relaxed" data-testid={testId}>
      <h1 className="text-3xl font-semibold tracking-tight">{title}</h1>
      <p className="mt-2 text-muted">{lead}</p>
      <div className="mt-8 space-y-6 [&_h2]:text-sm [&_h2]:font-semibold [&_h2]:uppercase [&_h2]:tracking-[0.04em] [&_h2]:text-muted [&_p]:mt-2 [&_section]:border-t [&_section]:border-line [&_section]:pt-4">
        {children}
      </div>
    </article>
  );
}
