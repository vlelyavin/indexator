"use client";

import { useRef, useEffect } from "react";
import { useTranslations } from "next-intl";
import { Globe, Link2, Loader2 } from "lucide-react";
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
  connected?: boolean;
  isPolling?: boolean;
}

/* ── Progress Ring ─────────────────────────────────────────── */

function ProgressRing({
  pct,
  size = 200,
  indeterminate = false,
}: {
  pct: number;
  size?: number;
  indeterminate?: boolean;
}) {
  const stroke = 8;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = indeterminate
    ? circumference * 0.75
    : circumference - (pct / 100) * circumference;

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
          className={cn(
            "transition-all duration-700 ease-out",
            indeterminate && "animate-spin-slow origin-center"
          )}
          style={indeterminate ? { animation: "spin 2s linear infinite", transformOrigin: `${size / 2}px ${size / 2}px` } : undefined}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        {indeterminate ? (
          <Loader2 className="h-8 w-8 animate-spin text-copper-light" />
        ) : (
          <span className="text-3xl font-bold text-white">
            {Math.round(pct)}%
          </span>
        )}
      </div>
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

function getPhaseLabel(
  progress: ProgressEvent | null,
  t: ReturnType<typeof useTranslations<"audit">>
): { title: string; subtitle: string } {
  if (!progress) return { title: t("progressConnecting"), subtitle: "" };

  const speedIsBlocking =
    progress.speed_blocking ||
    (progress.current_task_type === "speed" && progress.analyzer_phase === "running");
  if (speedIsBlocking) return { title: t("progressSpeedBlocking"), subtitle: "" };

  switch (progress.stage) {
    case "crawling":
      return {
        title: t("stageCrawling"),
        subtitle: progress.pages_crawled
          ? t("progressCrawling", { count: progress.pages_crawled })
          : t("progressCrawlingStart"),
      };
    case "analyzing": {
      const completed = progress.analyzers_completed ?? 0;
      const total = progress.analyzers_total ?? 0;
      return {
        title: t("stageAnalyzing"),
        subtitle: total > 0 ? `${completed} / ${total}` : "",
      };
    }
    case "report":
    case "generating_report":
      return { title: t("stageGeneratingReport"), subtitle: "" };
    default:
      return { title: t("progressConnecting"), subtitle: "" };
  }
}

/* ── Main Component ────────────────────────────────────────── */

export function AuditProgressView({
  progress,
  activityLog,
  status,
  connected,
  isPolling,
}: AuditProgressViewProps) {
  const t = useTranslations("audit");
  const pct = progress?.progress || 0;
  const logRef = useRef<HTMLDivElement>(null);
  const currentStage = getPipelineStage(progress);
  const isRunning = status !== "completed" && status !== "failed";
  const isCrawling = currentStage === "crawling";
  const phaseLabel = getPhaseLabel(progress, t);

  // Auto-scroll activity feed
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [activityLog.length]);

  const pipelineStages: { key: Stage; label: string }[] = [
    { key: "crawling", label: t("stageCrawling") },
    { key: "analyzing", label: t("stageAnalyzing") },
    { key: "report", label: t("stageGeneratingReport") },
  ];

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-950">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-800 p-4 sm:p-6">
        <h2 className="text-lg font-semibold text-white">{t("auditInProgress")}</h2>
        {connected && (
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-emerald-400">Live</span>
          </div>
        )}
        {!connected && isPolling && (
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            <span className="text-xs text-amber-400">Polling</span>
          </div>
        )}
      </div>

      {/* Body: two-column grid */}
      <div className="grid gap-6 p-4 sm:p-6 lg:grid-cols-2">
        {/* Left column: ring + metrics + pipeline */}
        <div className="space-y-6">
          {/* Progress ring with phase label */}
          <div className="flex flex-col items-center gap-3">
            <ProgressRing
              pct={pct}
              size={200}
              indeterminate={isCrawling}
            />
            <div className="text-center">
              <p className="text-base font-semibold text-white">{phaseLabel.title}</p>
              {phaseLabel.subtitle && (
                <p className="mt-0.5 text-sm text-gray-400">{phaseLabel.subtitle}</p>
              )}
            </div>
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

          {/* Horizontal pipeline */}
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center justify-between">
              {pipelineStages.map((stage, i) => {
                const state = getStageState(currentStage, stage.key);
                return (
                  <div key={stage.key} className="flex flex-1 items-center">
                    {/* Node */}
                    <div className="flex flex-col items-center gap-1.5">
                      <div
                        className={cn(
                          "h-3 w-3 rounded-full border-2",
                          state === "done" && "border-green-500 bg-green-500",
                          state === "active" && "border-copper-light bg-copper-light",
                          state === "upcoming" && "border-gray-600 bg-transparent"
                        )}
                      />
                      <span
                        className={cn(
                          "text-xs whitespace-nowrap",
                          state === "done" && "text-gray-400",
                          state === "active" && "font-medium text-white",
                          state === "upcoming" && "text-gray-600"
                        )}
                      >
                        {stage.label}
                      </span>
                    </div>
                    {/* Connecting line */}
                    {i < pipelineStages.length - 1 && (
                      <div className="mx-2 h-px flex-1 relative top-[-0.5rem]">
                        <div className="h-px w-full bg-gray-700" />
                        <div
                          className={cn(
                            "absolute top-0 left-0 h-px transition-all duration-700",
                            state === "done" ? "w-full bg-green-500/60" : state === "active" ? "w-1/2 bg-copper-light/60" : "w-0"
                          )}
                        />
                      </div>
                    )}
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
            className="flex-1 overflow-y-auto rounded-xl border border-gray-800 bg-gray-900 p-3 max-h-[500px]"
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
                    <span className="scanning-dot h-1.5 w-1.5 rounded-full bg-copper-light" />
                    <span className="text-xs text-gray-500">Scanning...</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* CSS animation for scanning indicator */}
      <style jsx>{`
        .scanning-dot {
          animation: scanning-pulse 1.5s ease-in-out infinite;
        }
        @keyframes scanning-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(0.75); }
        }
      `}</style>
    </div>
  );
}

/* ── Metric Card ──────────────────────────────────────────── */

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
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-3">
      <div className="flex items-center gap-2.5">
        <div className="rounded-lg bg-gray-800 p-2">
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
