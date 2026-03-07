"use client";

import { useRef, useEffect } from "react";
import { useTranslations } from "next-intl";
import { Globe, Link2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ProgressEvent } from "@/types/audit";

export interface ActivityEntry {
  id: string;
  type: "url" | "stage" | "analyzer" | "analyzer_done";
  label: string;
}

interface AuditProgressViewProps {
  progress: ProgressEvent | null;
  activityLog: ActivityEntry[];
  status?: string | null;
}

/* ── Progress Ring ─────────────────────────────────────────── */

function ProgressRing({ pct, size = 200 }: { pct: number; size?: number }) {
  const stroke = 8;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#262626"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-copper-light)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <span className="absolute text-3xl font-bold text-white">
        {Math.round(pct)}%
      </span>
    </div>
  );
}

/* ── Helpers ───────────────────────────────────────────────── */

type Stage = "crawling" | "analyzing" | "report";

function normalizeStage(raw?: string | null): Stage {
  if (!raw) return "crawling";
  if (raw === "generating_report" || raw === "report") return "report";
  if (raw === "analyzing") return "analyzing";
  return "crawling";
}

function getPipelineStage(progress: ProgressEvent | null): Stage {
  if (!progress) return "crawling";
  return normalizeStage(progress.stage);
}

function getStageState(current: Stage, target: Stage): "done" | "active" | "upcoming" {
  const order: Stage[] = ["crawling", "analyzing", "report"];
  const ci = order.indexOf(current);
  const ti = order.indexOf(target);
  if (ti < ci) return "done";
  if (ti === ci) return "active";
  return "upcoming";
}

function getProgressMessage(progress: ProgressEvent | null, t: ReturnType<typeof useTranslations<"audit">>): string {
  if (!progress) return t("progressConnecting");

  const speedIsBlocking =
    progress.speed_blocking ||
    (progress.current_task_type === "speed" && progress.analyzer_phase === "running");
  if (speedIsBlocking) return t("progressSpeedBlocking");

  switch (progress.stage) {
    case "crawling":
      return progress.pages_crawled
        ? t("progressCrawling", { count: progress.pages_crawled })
        : t("progressCrawlingStart");
    case "analyzing":
      return progress.current_task_type === "analyzing" &&
        progress.analyzer_name &&
        progress.analyzer_phase === "running"
        ? t("progressAnalyzingName", { name: progress.analyzer_name })
        : t("progressAnalyzing");
    case "report":
    case "generating_report":
      return t("progressGeneratingReport");
    default:
      return t("progressConnecting");
  }
}

/* ── Main Component ────────────────────────────────────────── */

export function AuditProgressView({ progress, activityLog, status }: AuditProgressViewProps) {
  const t = useTranslations("audit");
  const pct = progress?.progress || 0;
  const logRef = useRef<HTMLDivElement>(null);
  const currentStage = getPipelineStage(progress);
  const isRunning = status !== "completed" && status !== "failed";

  // Auto-scroll activity feed
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [activityLog.length]);

  // Analyzer progress description for pipeline
  function getAnalyzerDescription(): string {
    if (currentStage !== "analyzing" || !progress) return "";
    const completed = progress.analyzers_completed ?? 0;
    const total = progress.analyzers_total ?? 0;
    const count = total > 0 ? ` (${completed}/${total})` : "";
    if (progress.analyzer_name) return `${progress.analyzer_name}${count}`;
    if (total > 0) return `${completed}/${total} analyzers`;
    return "";
  }

  const pipelineStages: { key: Stage; label: string; description: string }[] = [
    { key: "crawling", label: t("stageCrawling"), description: currentStage === "crawling" ? getProgressMessage(progress, t) : "" },
    { key: "analyzing", label: t("stageAnalyzing"), description: getAnalyzerDescription() },
    { key: "report", label: t("stageGeneratingReport"), description: "" },
  ];

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-950">
      {/* Header */}
      <div className="border-b border-gray-800 p-4 sm:p-6">
        <h2 className="text-lg font-semibold text-white">{t("auditInProgress")}</h2>
      </div>

      {/* Body: two-column grid */}
      <div className="grid gap-6 p-4 sm:p-6 lg:grid-cols-2">
        {/* Left column: ring + metrics + pipeline */}
        <div className="space-y-6">
          {/* Progress ring */}
          <div className="flex justify-center">
            <ProgressRing pct={pct} size={200} />
          </div>

          {/* Metric cards */}
          {progress && (
            <div className="grid grid-cols-2 gap-3">
              <MetricCard
                icon={Globe}
                value={String(progress.pages_crawled || 0)}
                label={t("statPagesCrawled")}
              />
              <MetricCard
                icon={Link2}
                value={String(progress.links_found || 0)}
                label={t("statLinksFound")}
              />
            </div>
          )}

          {/* Pipeline stepper */}
          <div className="rounded-xl border border-gray-800 bg-gray-950 p-4">
            <div className="relative flex flex-col">
              {pipelineStages.map((stage, i) => {
                const state = getStageState(currentStage, stage.key);
                return (
                  <div key={stage.key} className="flex items-start gap-3">
                    {/* Dot + connector line */}
                    <div className="relative flex flex-col items-center">
                      <div
                        className={cn(
                          "relative z-10 h-3 w-3 rounded-full border-2 mt-0.5",
                          state === "done" && "border-green-500 bg-green-500",
                          state === "active" && "border-copper-light bg-copper-light",
                          state === "upcoming" && "border-gray-600 bg-transparent"
                        )}
                      />
                      {i < pipelineStages.length - 1 && (
                        <div
                          className={cn(
                            "w-px flex-1 min-h-4",
                            state === "done" ? "bg-green-500/40" : "bg-gray-700"
                          )}
                        />
                      )}
                    </div>
                    {/* Text */}
                    <div className={cn("min-w-0", i < pipelineStages.length - 1 && "pb-3")}>
                      <p
                        className={cn(
                          "text-sm font-medium",
                          state === "done" && "text-gray-400",
                          state === "active" && "text-white",
                          state === "upcoming" && "text-gray-600"
                        )}
                      >
                        {stage.label}
                      </p>
                      {state === "active" && stage.description && (
                        <p className="mt-0.5 truncate text-xs text-gray-500">{stage.description}</p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right column: activity feed */}
        <div className="flex flex-col">
          <h3 className="mb-3 text-sm font-medium text-gray-400">Live Activity</h3>
          <div
            ref={logRef}
            className="flex-1 overflow-y-auto rounded-xl border border-gray-800 bg-gray-950 p-3 max-h-[500px]"
          >
            {activityLog.length === 0 ? (
              <p className="py-8 text-center text-sm text-gray-600">{t("noActivityYet")}</p>
            ) : (
              <div className="space-y-1.5">
                {activityLog.map((entry) => (
                  <div key={entry.id} className="flex items-center gap-2 text-xs">
                    <span
                      className={cn(
                        "h-2 w-2 shrink-0 rounded-full",
                        entry.type === "url" && "bg-emerald-400",
                        entry.type === "stage" && "bg-gray-400",
                        entry.type === "analyzer" && "bg-copper-light",
                        entry.type === "analyzer_done" && "bg-emerald-400"
                      )}
                    />
                    <span
                      className={cn(
                        "truncate text-sm",
                        entry.type === "stage" ? "font-medium text-gray-200" : "text-gray-300"
                      )}
                    >
                      {entry.label}
                    </span>
                  </div>
                ))}
                {isRunning && (
                  <div className="flex items-center gap-2 py-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-copper-light animate-pulse" />
                    <span className="text-xs text-gray-500">Scanning...</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Metric Card (matches StatCard from audit-results) ───── */

function MetricCard({
  icon: Icon,
  value,
  label,
}: {
  icon: React.ComponentType<{ className?: string }>;
  value: string;
  label: string;
}) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-950 p-3">
      <div className="flex items-center gap-2.5">
        <div className="rounded-lg bg-gray-900 p-2">
          <Icon className="h-4 w-4 text-gray-400" />
        </div>
        <div className="min-w-0">
          <p className="text-lg font-bold text-white leading-tight">{value}</p>
          <p className="text-[11px] text-gray-500 leading-tight truncate">{label}</p>
        </div>
      </div>
    </div>
  );
}
