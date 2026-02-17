import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { toApiLogoPath } from "@/lib/logo-storage";

export async function GET() {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const user = await prisma.user.findUnique({
    where: { id: session.user.id },
    select: { planId: true },
  });

  if (!user || user.planId !== "agency") {
    return NextResponse.json(
      { error: "Agency plan required" },
      { status: 403 }
    );
  }

  const branding = await prisma.brandSettings.findUnique({
    where: { userId: session.user.id },
  });

  return NextResponse.json(branding);
}

export async function PUT(req: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Check plan
  const user = await prisma.user.findUnique({
    where: { id: session.user.id },
    select: { planId: true },
  });

  if (!user || user.planId !== "agency") {
    return NextResponse.json(
      { error: "Agency plan required" },
      { status: 403 }
    );
  }

  const body = await req.json();
  const { companyName, logoUrl } = body;

  // Validate companyName
  if (companyName !== undefined && companyName !== null) {
    if (typeof companyName !== "string" || companyName.length > 100) {
      return NextResponse.json(
        { error: "Company name must be a string under 100 characters" },
        { status: 400 }
      );
    }
  }

  let normalizedLogoUrl: string | undefined | null = logoUrl;

  // Validate + normalize logoUrl
  if (logoUrl !== undefined && logoUrl !== null && logoUrl !== "") {
    try {
      normalizedLogoUrl = toApiLogoPath(logoUrl);
      if (!normalizedLogoUrl) {
        return NextResponse.json(
          { error: "Invalid logo URL" },
          { status: 400 }
        );
      }
    } catch {
      return NextResponse.json(
        { error: "Invalid logo URL format" },
        { status: 400 }
      );
    }
  }

  const branding = await prisma.brandSettings.upsert({
    where: { userId: session.user.id },
    update: { companyName, logoUrl: normalizedLogoUrl },
    create: {
      userId: session.user.id,
      companyName,
      logoUrl: normalizedLogoUrl,
    },
  });

  return NextResponse.json(branding);
}
