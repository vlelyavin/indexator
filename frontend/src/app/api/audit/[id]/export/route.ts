import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { fastapiFetch } from "@/lib/api-client";
import {
  getPlanCapabilities,
  type ExportFormat,
} from "@/lib/plan-capabilities";

const SUPPORTED_FORMATS: ExportFormat[] = ["pdf", "html", "docx"];

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;
  const { searchParams } = new URL(req.url);
  const requestedFormat = (searchParams.get("format") || "pdf").toLowerCase();
  const lang = searchParams.get("lang");

  if (!SUPPORTED_FORMATS.includes(requestedFormat as ExportFormat)) {
    return NextResponse.json(
      { error: "Unsupported export format" },
      { status: 400 }
    );
  }
  const format = requestedFormat as ExportFormat;

  const user = await prisma.user.findUnique({
    where: { id: session.user.id },
    select: { planId: true },
  });

  if (!user) {
    return NextResponse.json({ error: "User not found" }, { status: 404 });
  }

  const capabilities = getPlanCapabilities(user.planId);
  if (!capabilities.allowedExportFormats.includes(format)) {
    return NextResponse.json(
      { error: "Your plan allows PDF export only" },
      { status: 403 }
    );
  }

  const audit = await prisma.audit.findUnique({ where: { id } });

  if (!audit || audit.userId !== session.user.id) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  let brand: Record<string, string> | undefined;
  if (capabilities.canUseBranding) {
    const branding = await prisma.brandSettings.findUnique({
      where: { userId: session.user.id },
    });
    if (branding) {
      const origin = new URL(req.url).origin;
      const logoUrl = branding.logoUrl
        ? branding.logoUrl.startsWith("http://") || branding.logoUrl.startsWith("https://")
          ? branding.logoUrl
          : `${origin}${branding.logoUrl.startsWith("/") ? branding.logoUrl : `/${branding.logoUrl}`}`
        : undefined;
      brand = {
        ...(branding.companyName ? { company_name: branding.companyName } : {}),
        ...(branding.primaryColor ? { primary_color: branding.primaryColor } : {}),
        ...(branding.accentColor ? { accent_color: branding.accentColor } : {}),
        ...(logoUrl ? { logo_url: logoUrl } : {}),
      };
      if (Object.keys(brand).length === 0) {
        brand = undefined;
      }
    }
  }

  // Build query params for FastAPI
  const queryParams = new URLSearchParams({ format });
  if (lang) queryParams.set("lang", lang);
  queryParams.set("show_watermark", String(capabilities.showWatermark));
  if (brand) {
    if (brand.company_name) queryParams.set("company_name", brand.company_name);
    if (brand.primary_color) queryParams.set("primary_color", brand.primary_color);
    if (brand.accent_color) queryParams.set("accent_color", brand.accent_color);
    if (brand.logo_url) queryParams.set("logo_url", brand.logo_url);
  }

  const fastapiRes = await fastapiFetch(
    `/api/audit/${audit.fastApiId}/download?${queryParams.toString()}`
  );

  // If FastAPI doesn't have the audit in memory anymore, regenerate from cached data
  if (fastapiRes.status === 404 && audit.resultJson) {
    const regenerateRes = await fastapiFetch("/api/report/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        format,
        audit: JSON.parse(audit.resultJson),
        language: lang || audit.language || "en",
        show_watermark: capabilities.showWatermark,
        brand,
      }),
    });

    if (!regenerateRes.ok) {
      return NextResponse.json(
        { error: "Report generation failed" },
        { status: regenerateRes.status }
      );
    }

    const contentType =
      regenerateRes.headers.get("content-type") || "application/octet-stream";
    const disposition =
      regenerateRes.headers.get("content-disposition") || "";
    const blob = await regenerateRes.arrayBuffer();

    return new NextResponse(blob, {
      headers: {
        "Content-Type": contentType,
        "Content-Disposition": disposition,
      },
    });
  }

  if (!fastapiRes.ok) {
    return NextResponse.json(
      { error: "Export failed" },
      { status: fastapiRes.status }
    );
  }

  const contentType = fastapiRes.headers.get("content-type") || "application/octet-stream";
  const disposition = fastapiRes.headers.get("content-disposition") || "";
  const blob = await fastapiRes.arrayBuffer();

  return new NextResponse(blob, {
    headers: {
      "Content-Type": contentType,
      "Content-Disposition": disposition,
    },
  });
}
