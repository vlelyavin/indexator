"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

const FAQ_COUNT = 7;

export function IndexingFaqSection() {
  const t = useTranslations("marketing.indexingLanding.faq");
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="bg-black py-24">
      <div className="mx-auto max-w-3xl px-4 lg:px-6">
        <p className="mb-2 text-center font-bold bg-gradient-to-r from-copper to-copper-light bg-clip-text text-transparent" style={{ fontSize: "clamp(1rem, 1.8vw, 1.8rem)" }}>
          {t("sectionLabel")}
        </p>
        <h2 className="text-center font-bold text-white" style={{ fontSize: "clamp(2rem, 4vw, 4rem)", lineHeight: 1.2 }}>
          {t("title")}
        </h2>

        <div className="mt-12 space-y-4">
          {Array.from({ length: FAQ_COUNT }, (_, i) => i + 1).map((i) => {
            const isOpen = openIndex === i;
            return (
              <div
                key={i}
                className="rounded-xl border border-gray-800 bg-gray-950"
              >
                <button
                  onClick={() => setOpenIndex(isOpen ? null : i)}
                  className="flex w-full items-center justify-between px-6 py-5 text-left"
                >
                  <span className="font-bold text-white" style={{ fontSize: "clamp(1rem, 1.5vw, 1.5rem)" }}>
                    {t(`q${i}`)}
                  </span>
                  <motion.span
                    animate={{ rotate: isOpen ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ChevronDown className="h-5 w-5 shrink-0 text-gray-500" />
                  </motion.span>
                </button>
                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25, ease: "easeInOut" }}
                      className="overflow-hidden"
                    >
                      <div className="border-t border-gray-800 px-6 pb-5 pt-4">
                        <p className="font-medium text-[#e9e9e9]" style={{ fontSize: "clamp(0.8rem, 1.1vw, 1.1rem)", lineHeight: "150%" }}>
                          {t(`a${i}`)}
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
