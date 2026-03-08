"use client";

import { useState, useEffect, useCallback } from "react";
import { Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import {
  Plus,
  BarChart3,
  Globe,
  Calendar,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  AlertCircle,
  AlertTriangle,
} from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import type { AuditSummary } from "@/types/audit";

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const tBreadcrumbs = useTranslations("breadcrumbs");
  const [audits, setAudits] = useState<AuditSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAudits = useCallback(async () => {
    try {
      const res = await fetch("/api/audit/list?take=5");
      if (res.ok) {
        setAudits(await res.json());
      }
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAudits();
  }, [fetchAudits]);

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-400" />;
      case "failed":
        return <XCircle className="h-5 w-5 shrink-0 text-red-400" />;
      case "pending":
        return <Clock className="h-5 w-5 shrink-0 text-gray-400" />;
      default:
        return <Loader2 className="h-5 w-5 shrink-0 animate-spin text-copper" />;
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const shortenUrl = (url: string) => {
    try {
      const u = new URL(url);
      return u.hostname + (u.pathname !== "/" ? u.pathname : "");
    } catch {
      return url;
    }
  };

  const completed = audits.filter((a) => a.status === "completed");
  const totalAudits = audits.length;
  const avgScore =
    completed.length > 0
      ? Math.round(
          completed.reduce((sum, a) => sum + a.passedChecks, 0) / completed.length
        )
      : 0;
  const lastAuditDate =
    audits.length > 0 ? formatDate(audits[0].startedAt) : "—";

  if (loading) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-white border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Breadcrumbs items={[{ label: tBreadcrumbs("dashboard") }]} />
          <h1 className="text-2xl font-bold text-white">{tBreadcrumbs("dashboard")}</h1>
        </div>
        <Link
          href="/app/auditor/new"
          className="flex items-center gap-2 rounded-md bg-gradient-to-r from-copper to-copper-light px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90"
        >
          <Plus className="h-4 w-4" />
          {t("startAudit")}
        </Link>
      </div>

      {/* Stats row */}
      {audits.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-xl border border-gray-800 bg-gray-950 p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-gray-900 p-2 text-white">
                <BarChart3 className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{totalAudits}</p>
                <p className="text-xs text-gray-400">Total Audits</p>
              </div>
            </div>
          </div>
          <div className="rounded-xl border border-gray-800 bg-gray-950 p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-gray-900 p-2 text-white">
                <Globe className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{avgScore}</p>
                <p className="text-xs text-gray-400">Avg Passed Checks</p>
              </div>
            </div>
          </div>
          <div className="rounded-xl border border-gray-800 bg-gray-950 p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-gray-900 p-2 text-white">
                <Calendar className="h-5 w-5" />
              </div>
              <div>
                <p className="text-lg font-bold text-white">{lastAuditDate}</p>
                <p className="text-xs text-gray-400">Last Audit</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent audits */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">{t("recentAudits")}</h2>
          {audits.length > 0 && (
            <Link
              href="/app/auditor"
              className="text-sm text-gray-400 transition-colors hover:text-copper-light"
            >
              View all
            </Link>
          )}
        </div>

        {audits.length === 0 ? (
          <div className="rounded-xl border border-gray-800 bg-gray-950 p-12 text-center">
            <Globe className="mx-auto mb-4 h-12 w-12 text-gray-600" />
            <p className="text-sm text-gray-400">{t("noAudits")}</p>
            <Link
              href="/app/auditor/new"
              className="mt-4 inline-flex items-center gap-2 rounded-md bg-gradient-to-r from-copper to-copper-light px-6 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90"
            >
              <Plus className="h-4 w-4" />
              {t("startAudit")}
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {audits.map((audit) => (
              <Link
                key={audit.id}
                href={`/app/auditor/${audit.id}`}
                className="block rounded-xl border border-gray-800 bg-gray-950 p-3 md:p-4 transition-colors hover:border-gray-700"
              >
                <div className="flex items-center gap-3">
                  {statusIcon(audit.status)}
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-white">
                      {shortenUrl(audit.url)}
                    </p>
                    <div className="mt-1 flex items-center gap-x-3 text-xs text-gray-500">
                      <span>{formatDate(audit.startedAt)}</span>
                      {audit.status === "completed" && (
                        <span>{audit.pagesCrawled} pages</span>
                      )}
                    </div>
                  </div>
                  {audit.status === "completed" && (audit.criticalIssues > 0 || audit.warnings > 0) && (
                    <div className="flex items-center gap-3">
                      {audit.criticalIssues > 0 && (
                        <span className="flex items-center gap-1 text-xs font-medium text-red-400">
                          <AlertCircle className="h-3 w-3" />
                          {audit.criticalIssues}
                        </span>
                      )}
                      {audit.warnings > 0 && (
                        <span className="flex items-center gap-1 text-xs font-medium text-yellow-400">
                          <AlertTriangle className="h-3 w-3" />
                          {audit.warnings}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
