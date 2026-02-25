"use client";

import { Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import { ArrowRight, ScanSearch } from "lucide-react";
import Image from "next/image";

export function HeroSection() {
  const t = useTranslations("marketing.landing");

  return (
    <section className="relative overflow-hidden bg-black pt-24 pb-20">
      {/* Gradient mesh background */}
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div className="absolute top-0 left-1/2 h-[600px] w-[900px] -translate-x-1/2 rounded-full bg-[radial-gradient(ellipse_at_center,rgba(184,115,51,0.12)_0%,transparent_60%)] blur-3xl" />
        <div className="absolute -top-32 -left-40 h-[500px] w-[500px] rounded-full bg-[radial-gradient(circle,rgba(184,115,51,0.08)_0%,transparent_70%)] blur-3xl" />
        <div className="absolute top-20 -right-32 h-[400px] w-[400px] rounded-full bg-[radial-gradient(circle,rgba(120,80,40,0.06)_0%,transparent_70%)] blur-3xl" />
        <div className="absolute bottom-0 left-1/2 h-[200px] w-full -translate-x-1/2 bg-gradient-to-t from-black to-transparent" />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48ZmlsdGVyIGlkPSJuIj48ZmVUdXJidWxlbmNlIHR5cGU9ImZyYWN0YWxOb2lzZSIgYmFzZUZyZXF1ZW5jeT0iMC44IiBudW1PY3RhdmVzPSI0IiBzdGl0Y2hUaWxlcz0ic3RpdGNoIi8+PC9maWx0ZXI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsdGVyPSJ1cmwoI24pIiBvcGFjaXR5PSIwLjAzIi8+PC9zdmc+')] opacity-50" />
      </div>

      <div className="relative mx-auto max-w-5xl px-4 lg:px-6">
        <div className="flex flex-col items-center text-center">
          <p className="mb-4 text-sm font-medium not-italic text-copper">
            {t("sectionLabel")}
          </p>
          <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
            {t("title")}
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-gray-400">
            {t("subtitle")}
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              href="/dashboard/auditor/new"
              className="inline-flex items-center justify-center gap-2 rounded-md bg-gradient-to-r from-copper to-copper-light px-8 py-3.5 text-center text-sm font-semibold text-white transition-opacity hover:opacity-90"
            >
              <ScanSearch className="h-4 w-4" />
              {t("cta")}
            </Link>
            <Link
              href="/pricing"
              className="inline-flex items-center justify-center gap-1 rounded-md border border-gray-700 px-8 py-3.5 text-center text-sm font-semibold text-white transition-colors hover:bg-black"
            >
              {t("viewPricing")} <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </div>
        </div>

        <div className="mt-16">
          <Image
            src="/images/seo-audit-dashboard-screenshot.png"
            alt={t("title")}
            width={1920}
            height={1080}
            className="w-full"
            priority
          />
        </div>
      </div>
    </section>
  );
}
