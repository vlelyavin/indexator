"use client";

import { Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import { ArrowRight, Zap } from "lucide-react";
import Image from "next/image";

export function IndexingHeroSection() {
  const t = useTranslations("marketing.indexingLanding.hero");

  return (
    <section className="relative mx-auto max-w-5xl px-4 pt-24 pb-20 lg:px-6">
      {/* Copper radial glow behind heading */}
      <div
        className="pointer-events-none absolute top-16 left-1/2 -translate-x-1/2"
        aria-hidden="true"
      >
        <div className="h-[500px] w-[700px] rounded-full bg-[radial-gradient(ellipse_at_center,rgba(184,115,51,0.15)_0%,rgba(184,115,51,0.05)_40%,transparent_70%)] blur-2xl" />
      </div>

      <div className="relative flex flex-col items-center text-center">
        <span className="mb-4 inline-flex items-center rounded-full border border-copper/30 bg-copper/10 px-3 py-1 text-xs font-medium text-copper">
          {t("sectionLabel")}
        </span>
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
          {t("title")}
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-gray-400">
          {t("subtitle")}
        </p>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <Link
            href="/dashboard/indexator"
            className="inline-flex items-center justify-center gap-2 rounded-md bg-gradient-to-r from-copper to-copper-light px-8 py-3.5 text-center text-sm font-semibold text-white transition-opacity hover:opacity-90"
          >
            <Zap className="h-4 w-4" />
            {t("ctaPrimary")}
          </Link>
          <a
            href="#pricing"
            className="rounded-md border border-gray-700 px-8 py-3.5 text-center text-sm font-semibold text-white transition-colors hover:bg-black"
          >
            {t("ctaSecondary")} <ArrowRight className="ml-1 inline h-4 w-4" />
          </a>
        </div>
      </div>

      <div className="mt-16">
        <Image
          src="/images/indexing-dashboard-screenshot.png"
          alt={t("title")}
          width={1920}
          height={1080}
          className="w-full"
          priority
        />
      </div>
    </section>
  );
}
