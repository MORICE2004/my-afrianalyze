"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import { EASE, T } from "@/components/motion/primitives";
import { useToast } from "@/components/ui/Toast";
import { saveConsent, useConsent } from "@/lib/consent";

// A compact banner on a first visit, and a preferences dialog the footer can reopen. Accept and reject are the
// same size and weight: neither is nudged.
export function CookieConsent() {
  const consent = useConsent();
  const reduce = useReducedMotion();
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [analytics, setAnalytics] = useState(false);

  useEffect(() => {
    const show = () => {
      setAnalytics(!!consent?.analytics);
      setOpen(true);
    };
    window.addEventListener("afriedge:cookie-preferences", show);
    return () => window.removeEventListener("afriedge:cookie-preferences", show);
  }, [consent]);

  const decide = (a: boolean, message: string) => {
    saveConsent(a);
    setOpen(false);
    toast(message);
  };
  const btn = "inline-flex h-10 items-center justify-center rounded-md border border-line-strong bg-surface px-4 text-sm font-medium text-fg transition-colors hover:bg-surface-2";

  return (
    <>
      <AnimatePresence>
        {consent === null && !open && (
          <motion.section role="region" aria-label="Cookie preferences" data-testid="cookie-banner"
            initial={reduce ? false : { opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}
            transition={{ duration: T.base, ease: EASE }}
            className="fixed inset-x-3 bottom-3 z-[60] mx-auto max-w-3xl rounded-lg border border-line bg-surface p-4 shadow-xl sm:inset-x-6 sm:p-5 lg:left-6 lg:right-auto lg:mx-0 lg:max-w-[36rem]"
            style={{ marginBottom: "env(safe-area-inset-bottom, 0px)" }}>
            <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between lg:flex-col lg:items-stretch">
              <div className="max-w-xl">
                <h2 className="text-sm font-semibold">Your privacy matters</h2>
                <p className="mt-1 text-sm leading-relaxed text-muted">
                  We use essential cookies to operate AfriEdge. With your permission, we also record usage analytics to
                  improve the experience. <Link href="/cookies" className="text-fg underline underline-offset-4">Cookie policy</Link>
                </p>
              </div>
              <div className="grid shrink-0 grid-cols-3 gap-2 sm:flex">
                <button type="button" className={btn} onClick={() => decide(false, "Optional analytics turned off")} data-testid="cookie-reject">Reject optional</button>
                <button type="button" className={btn} onClick={() => { setAnalytics(false); setOpen(true); }} data-testid="cookie-customize">Customize</button>
                <button type="button" className={btn} onClick={() => decide(true, "Preferences saved")} data-testid="cookie-accept">Accept all</button>
              </div>
            </div>
          </motion.section>
        )}
      </AnimatePresence>

      <Dialog.Root open={open} onOpenChange={setOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-[80] bg-black/30 data-[state=open]:animate-[pop_0.15s_ease-out]" />
          <Dialog.Content data-testid="cookie-dialog"
            className="fixed left-1/2 top-1/2 z-[81] w-[min(30rem,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 rounded-lg border border-line bg-surface p-5 shadow-2xl data-[state=open]:animate-[pop_0.18s_ease-out]">
            <Dialog.Title className="text-base font-semibold">Cookie preferences</Dialog.Title>
            <Dialog.Description className="mt-1 text-sm text-muted">
              Choose which optional technologies AfriEdge may use. You can change this at any time from the footer.
            </Dialog.Description>
            <ul className="mt-4 divide-y divide-line border-y border-line text-sm">
              <li className="flex items-start justify-between gap-4 py-3">
                <span>
                  <span className="font-medium">Necessary</span>
                  <span className="mt-0.5 block text-xs text-muted">Sign-in session, security checks, this choice and your theme.</span>
                </span>
                <span className="shrink-0 text-xs font-medium text-muted">Always on</span>
              </li>
              <li className="flex items-start justify-between gap-4 py-3">
                <label htmlFor="consent-analytics" className="cursor-pointer">
                  <span className="font-medium">Analytics</span>
                  <span className="mt-0.5 block text-xs text-muted">Which pages and features are used, under a scrambled identifier, never your email. No advertising.</span>
                </label>
                <button id="consent-analytics" type="button" role="switch" aria-checked={analytics} onClick={() => setAnalytics((a) => !a)}
                  data-testid="consent-analytics"
                  className={`relative mt-0.5 h-6 w-10 shrink-0 rounded-full transition-colors ${analytics ? "bg-selected" : "bg-line-strong"}`}>
                  <span className={`absolute left-0 top-0.5 h-5 w-5 rounded-full bg-surface shadow transition-transform ${analytics ? "translate-x-[18px]" : "translate-x-0.5"}`} />
                </button>
              </li>
            </ul>
            <div className="mt-4 flex flex-wrap justify-end gap-2">
              <button type="button" className={btn} onClick={() => decide(false, "Optional analytics turned off")}>Reject optional</button>
              <button type="button" className={btn} onClick={() => decide(analytics, "Preferences saved")} data-testid="consent-save">Save preferences</button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
