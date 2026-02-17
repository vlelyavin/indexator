import { existsSync } from "fs";
import { join, resolve } from "path";

const FILENAME_RE = /^[a-zA-Z0-9_.-]+$/;

function isFrontendRoot(dir: string): boolean {
  return (
    existsSync(join(dir, "next.config.js")) ||
    existsSync(join(dir, "next.config.ts")) ||
    existsSync(join(dir, "app")) ||
    existsSync(join(dir, "src"))
  );
}

export function getFrontendRootDir(): string {
  const envRoot = process.env.FRONTEND_ROOT?.trim();
  if (envRoot) {
    return envRoot;
  }

  const cwd = process.cwd();
  const candidates = [
    cwd,
    resolve(cwd, ".."),
    resolve(cwd, "../.."),
    resolve(cwd, "../../.."),
  ];

  for (const candidate of candidates) {
    if (isFrontendRoot(candidate)) {
      return candidate;
    }
  }

  if (isFrontendRoot(join(cwd, "frontend"))) {
    return join(cwd, "frontend");
  }

  return cwd;
}

export function getUploadsDir(): string {
  return join(getFrontendRootDir(), "public", "uploads");
}

export function extractLogoFilenameFromUrl(logoUrl?: string | null): string | null {
  if (!logoUrl) return null;

  let pathname = logoUrl;
  try {
    pathname = new URL(logoUrl, "https://placeholder.local").pathname;
  } catch {
    return null;
  }

  let raw = "";
  if (pathname.startsWith("/api/upload/logo/")) {
    raw = pathname.slice("/api/upload/logo/".length);
  } else if (pathname.startsWith("/uploads/")) {
    raw = pathname.slice("/uploads/".length);
  } else {
    return null;
  }

  return FILENAME_RE.test(raw) ? raw : null;
}

export function toApiLogoPath(logoUrl?: string | null): string | null {
  const filename = extractLogoFilenameFromUrl(logoUrl);
  return filename ? `/api/upload/logo/${filename}` : null;
}

