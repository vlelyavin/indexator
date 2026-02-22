import { NextRequest, NextResponse } from "next/server";
import createIntlMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

const intlMiddleware = createIntlMiddleware(routing);

const locales = routing.locales;

/**
 * Check for Auth.js v5 session cookie. This is a lightweight presence
 * check — actual JWT verification happens in page/API auth() calls.
 */
function hasSessionCookie(req: NextRequest): boolean {
  return !!(
    req.cookies.get("authjs.session-token") ||
    req.cookies.get("__Secure-authjs.session-token")
  );
}

function stripLocale(pathname: string): string {
  for (const locale of locales) {
    if (pathname === `/${locale}`) return "/";
    if (pathname.startsWith(`/${locale}/`))
      return pathname.slice(locale.length + 1);
  }
  return pathname;
}

function getLocale(pathname: string): string {
  for (const locale of locales) {
    if (pathname === `/${locale}` || pathname.startsWith(`/${locale}/`)) {
      return locale;
    }
  }
  return routing.defaultLocale;
}

export default async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const path = stripLocale(pathname);

  // Dashboard routes: require authentication
  if (path.startsWith("/dashboard")) {
    if (!hasSessionCookie(req)) {
      const locale = getLocale(pathname);
      return NextResponse.redirect(new URL(`/${locale}/login`, req.url));
    }
  }

  // Auth pages: redirect authenticated users to dashboard
  if (path === "/login" || path === "/register") {
    if (hasSessionCookie(req)) {
      const locale = getLocale(pathname);
      return NextResponse.redirect(new URL(`/${locale}/dashboard`, req.url));
    }
  }

  // All other routes (landing, pricing, indexing, etc.): pass through
  return intlMiddleware(req);
}

export const config = {
  matcher: [
    // Match all pathnames except for
    // - api routes
    // - _next (Next.js internals)
    // - static files (images, etc.)
    "/((?!api|_next|.*\\..*).*)",
  ],
};
