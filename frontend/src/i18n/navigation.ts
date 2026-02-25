import { createNavigation } from "next-intl/navigation";
import { routing } from "./routing";

export const { Link, redirect, usePathname, useRouter } =
  createNavigation(routing);

/**
 * Build a locale-aware path string for non-component contexts
 * (NextAuth callbacks, emails, etc.).
 * Always includes /{locale} prefix.
 */
export function localePath(locale: string, path: string): string {
  return `/${locale}${path}`;
}
