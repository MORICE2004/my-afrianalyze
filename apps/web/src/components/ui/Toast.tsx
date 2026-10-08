"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import React, { createContext, useCallback, useContext, useState } from "react";
import { EASE, T } from "@/components/motion/primitives";

// Short confirmations ("Saved", "Exported") at the bottom of the screen. Announced to screen readers through a
// polite live region; they dismiss themselves after four seconds and never block the page.
type Toast = { id: number; text: string; tone: "ok" | "error" };
const Ctx = createContext<(text: string, tone?: Toast["tone"]) => void>(() => {});

export function useToast() {
  return useContext(Ctx);
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const reduce = useReducedMotion();
  const push = useCallback((text: string, tone: Toast["tone"] = "ok") => {
    const id = Date.now() + Math.random();
    setItems((xs) => [...xs.slice(-2), { id, text, tone }]);
    setTimeout(() => setItems((xs) => xs.filter((x) => x.id !== id)), 4000);
  }, []);
  return (
    <Ctx.Provider value={push}>
      {children}
      <div aria-live="polite" role="status" className="pointer-events-none fixed inset-x-0 bottom-4 z-[70] flex flex-col items-center gap-2 px-4"
        style={{ paddingBottom: "env(safe-area-inset-bottom, 0px)" }}>
        <AnimatePresence>
          {items.map((t) => (
            <motion.div key={t.id} data-testid="toast"
              initial={reduce ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }}
              transition={{ duration: T.fast, ease: EASE }}
              className={`pointer-events-auto rounded-md px-3.5 py-2 text-sm shadow-lg ${t.tone === "error" ? "bg-neg text-white" : "bg-selected text-on-selected"}`}>
              {t.text}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </Ctx.Provider>
  );
}
