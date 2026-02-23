import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { getGoogleAccount } from "@/lib/google-auth";

/**
 * DELETE /api/indexing/gsc/disconnect
 * Revokes the user's Google token and clears GSC connection state.
 * Query params:
 *   - deleteData: "true" (default) deletes all sites + URLs; "false" keeps data (OAuth only)
 */
export async function DELETE(req: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { searchParams } = new URL(req.url);
  const deleteData = searchParams.get("deleteData") !== "false";

  const account = await getGoogleAccount(session.user.id);

  // Revoke token with Google
  if (account?.access_token) {
    try {
      await fetch(
        `https://oauth2.googleapis.com/revoke?token=${account.access_token}`,
        { method: "POST" }
      );
    } catch {
      // Non-fatal — proceed with local cleanup even if revocation fails
    }
  }

  // Clear OAuth tokens from Account record (keep provider link so user can sign in)
  if (account) {
    await prisma.account.update({
      where: { id: account.id },
      data: {
        access_token: null,
        refresh_token: null,
        expires_at: null,
        scope: null,
      },
    });
  }

  // Clear GSC state; optionally wipe sites + URLs
  if (deleteData) {
    await prisma.$transaction([
      prisma.user.update({
        where: { id: session.user.id },
        data: { gscConnected: false, gscConnectedAt: null },
      }),
      prisma.site.deleteMany({ where: { userId: session.user.id } }),
    ]);
  } else {
    await prisma.user.update({
      where: { id: session.user.id },
      data: { gscConnected: false, gscConnectedAt: null },
    });
  }

  return NextResponse.json({ success: true });
}
