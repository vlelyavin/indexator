import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function DELETE() {
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

  await prisma.brandSettings.updateMany({
    where: { userId: session.user.id },
    data: { logoUrl: null },
  });

  return NextResponse.json({ ok: true });
}
