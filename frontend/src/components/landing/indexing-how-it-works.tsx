"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";

export function IndexingHowItWorks() {
  const t = useTranslations("marketing.indexingLanding.howItWorks");

  const steps = [
    { num: "01", title: t("step1Title"), desc: t("step1Desc") },
    { num: "02", title: t("step2Title"), desc: t("step2Desc") },
    { num: "03", title: t("step3Title"), desc: t("step3Desc") },
  ];

  return (
    <section className="bg-black" style={{ padding: "clamp(1rem, 4vw, 4rem)" }}>
      <div className="mx-auto w-full text-center" style={{ maxWidth: "800px" }}>
        <p className="mb-2 text-center font-bold bg-gradient-to-r from-copper to-copper-light bg-clip-text text-transparent" style={{ fontSize: "clamp(1rem, 1.8vw, 1.8rem)" }}>
          {t("sectionLabel")}
        </p>
        <h2 className="text-center font-bold text-white" style={{ fontSize: "clamp(2rem, 4vw, 4rem)", lineHeight: 1.2, marginBottom: "1.5rem" }}>
          {t("title")}
        </h2>

        <div className="flex flex-col text-left" style={{ gap: "clamp(1.5rem, 2.5vw, 2.5rem)", marginTop: "1.5rem" }}>
          {steps.map((step, i) => (
            <motion.div
              key={step.num}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: i * 0.15 }}
              className="flex items-start border-t border-[#282828] max-[800px]:flex-col max-[800px]:items-center max-[800px]:text-center"
              style={{ paddingTop: "clamp(1.5rem, 2.5vw, 2.5rem)", gap: "clamp(1rem, 2vw, 2rem)" }}
            >
              <span
                className="shrink-0 font-bold leading-none bg-gradient-to-b from-copper-light to-copper bg-clip-text text-transparent"
                style={{ fontSize: "clamp(2rem, 3.5vw, 3.5rem)", minWidth: "3.5rem" }}
              >
                {step.num}
              </span>
              <div className="flex flex-col" style={{ gap: "0.5rem" }}>
                <h3 className="font-bold text-white" style={{ fontSize: "clamp(1rem, 1.5vw, 1.5rem)" }}>
                  {step.title}
                </h3>
                <p className="font-medium text-[#e9e9e9]" style={{ fontSize: "clamp(0.8rem, 1.1vw, 1.1rem)", lineHeight: "150%" }}>
                  {step.desc}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
