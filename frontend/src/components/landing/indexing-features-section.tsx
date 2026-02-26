"use client";

import { useTranslations } from "next-intl";
import {
  BarChart3,
  MousePointerClick,
  RefreshCw,
  ShieldAlert,
  Mail,
  Lightbulb,
} from "lucide-react";
import { motion } from "framer-motion";

const ICONS = [BarChart3, MousePointerClick, RefreshCw, ShieldAlert, Mail, Lightbulb];

export function IndexingFeaturesSection() {
  const t = useTranslations("marketing.indexingLanding.features");

  const features = Array.from({ length: 6 }, (_, i) => ({
    title: t(`feature${i + 1}Title`),
    desc: t(`feature${i + 1}Desc`),
    icon: ICONS[i],
  }));

  return (
    <section className="bg-black py-24">
      <div className="mx-auto max-w-6xl px-4 lg:px-6">
        <p className="mb-2 text-center font-bold bg-gradient-to-r from-copper to-copper-light bg-clip-text text-transparent" style={{ fontSize: "clamp(1rem, 1.8vw, 1.8rem)" }}>
          {t("sectionLabel")}
        </p>
        <h2 className="text-center font-bold text-white" style={{ fontSize: "clamp(2rem, 4vw, 4rem)", lineHeight: 1.2 }}>
          {t("title")}
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-center font-medium text-[#e9e9e9]" style={{ fontSize: "clamp(.8rem, 1.25vw, 1.25rem)", lineHeight: "150%" }}>
          {t("subtitle")}
        </p>

        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feat, i) => (
            <motion.div
              key={feat.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="group rounded-xl border border-gray-800 bg-gray-950 p-8 transition-colors hover:border-copper/30"
            >
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-lg bg-copper/10">
                <feat.icon className="h-6 w-6 text-copper" />
              </div>
              <h3 className="font-bold text-white" style={{ fontSize: "clamp(1rem, 1.5vw, 1.5rem)" }}>{feat.title}</h3>
              <p className="mt-3 font-medium text-[#e9e9e9]" style={{ fontSize: "clamp(0.8rem, 1.1vw, 1.1rem)", lineHeight: "150%" }}>
                {feat.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
