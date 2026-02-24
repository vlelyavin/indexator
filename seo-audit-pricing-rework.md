# SEO Audit — Pricing Page Rework

## 1. Remove the "How it works" intro cards

Delete the three cards at the top of the pricing page ("Choose a Plan", "Use Credits", "Need More?"). They add no value — they just describe what a pricing page does.

Replace them with a single headline + one-sentence explanation:

**Heading:** "Two tools. Two pricing models."
**Subheading:** "Audit subscriptions cover your SEO analysis. Indexing credits cover Google URL submissions. Pick what you need."

Add translation keys for all 3 locales (en, ru, uk). Keep it this short — no fluff.

## 2. Restructure the two pricing sections with clear visual separation

Currently both sections (audit plans + indexing credits) are stacked with similar styling, making them blur together.

**Fix:**
- **Section 1: "SEO Audit Plans"** — heading + one-liner description ("Run unlimited audits, export reports, white-label for clients.") + the 3 plan cards (Free / Pro / Agency) in a row
- **Visual separator** — use a different background shade or add generous spacing between sections so they feel like two distinct blocks
- **Section 2: "Indexing Credits"** — heading + one-liner description ("Submit URLs to Google for indexing. IndexNow submissions are always free.") + the 2 credit pack cards

Each section should feel self-contained. A user should be able to glance at the page and immediately understand there are two separate things being sold.

Update all translation keys for en, ru, uk.

## 3. Remove duplicate text

The page currently has text duplicates:
- "Pricing" appears multiple times as a section label/subtitle
- The IndexNow free disclaimer appears twice in different forms
- "No watermark in exported reports" could be implied by just listing it on Pro/Agency and saying "Watermark" on Free

Audit the entire pricing page content and remove any duplicate or near-duplicate text. Each piece of information should appear exactly once.

## 4. Localization

Every new or changed string must have translation keys in all three locale files (en.json, ru.json, uk.json). Search for any hardcoded English strings on the pricing page and move them to translation files if they aren't already.

Commit when done.
