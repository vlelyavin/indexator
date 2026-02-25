"use client";

import { useTranslations } from "next-intl";
import { Link2, Search, Send } from "lucide-react";
import { motion } from "framer-motion";

const STEP_ICONS = [Link2, Search, Send] as const;

export function IndexingHowItWorks() {
  const t = useTranslations("marketing.indexingLanding.howItWorks");

  const steps = [
    { icon: STEP_ICONS[0], title: t("step1Title"), desc: t("step1Desc") },
    { icon: STEP_ICONS[1], title: t("step2Title"), desc: t("step2Desc") },
    { icon: STEP_ICONS[2], title: t("step3Title"), desc: t("step3Desc") },
  ];

  return (
    <section className="bg-black py-24">
      <div className="mx-auto max-w-5xl px-4 lg:px-6">
        <p className="mb-4 text-center text-sm font-medium not-italic text-copper">
          {t("sectionLabel")}
        </p>
        <h2 className="text-center text-3xl font-bold text-white sm:text-4xl lg:text-5xl">
          {t("title")}
        </h2>

        <div className="relative mt-20">
          {/* Connector line (desktop only) */}
          <div className="pointer-events-none absolute top-10 right-[calc(16.67%+24px)] left-[calc(16.67%+24px)] hidden sm:block" aria-hidden="true">
            <div className="h-px w-full border-t border-dashed border-copper/25" />
          </div>

          <div className="grid gap-12 sm:grid-cols-3 sm:gap-8">
            {steps.map((step, i) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: i * 0.15 }}
                className="flex flex-col items-center text-center"
              >
                <div className="relative z-10 flex h-20 w-20 items-center justify-center rounded-full border border-copper/20 bg-gray-950">
                  <step.icon className="h-8 w-8 text-copper" />
                </div>
                <h3 className="mt-6 text-lg font-semibold text-white">
                  {step.title}
                </h3>
                <p className="mt-3 max-w-xs leading-relaxed text-gray-400">
                  {step.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
