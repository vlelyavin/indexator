"""Hreflang and international SEO analyzer."""

from typing import Any, Dict, List, Set

from ..models import AnalyzerResult, AuditIssue, PageData, SeverityLevel
from .base import BaseAnalyzer


# Basic ISO 639-1 language codes
VALID_LANG_CODES = {
    "uk", "ru", "en", "de", "fr", "es", "it", "pl", "pt", "nl",
    "sv", "da", "no", "fi", "cs", "sk", "hu", "ro", "bg", "hr",
    "sl", "sr", "bs", "mk", "sq", "el", "tr", "ar", "he", "ja",
    "zh", "ko", "th", "vi", "id", "ms", "hi", "bn", "ka", "az",
    "kk", "uz", "be", "lt", "lv", "et", "mt", "ga", "cy", "is",
    "x-default",
}


class HreflangAnalyzer(BaseAnalyzer):
    """Analyzer for hreflang tags and international SEO setup."""

    name = "hreflang"
    display_name = "Hreflang"
    description = "Аналіз налаштувань мультимовних та регіональних версій сторінок."
    icon = ""
    theory = """<strong>Hreflang</strong> — атрибут, що вказує пошуковим системам на мовні та регіональні версії сторінки. Використовується у тезі <code>&lt;link rel="alternate" hreflang="xx" href="URL"&gt;</code>.

<strong>Основні правила:</strong>
• Кожна сторінка повинна мати <strong>самопосилання</strong> (self-referencing) — hreflang, що вказує на саму себе
• Теги мають бути <strong>двосторонніми</strong>: якщо A посилається на B, то B повинна посилатися на A
• Використовуйте коди мов за стандартом <strong>ISO 639-1</strong> (uk, en, de, fr тощо)
• Додайте <code>x-default</code> для версії за замовчуванням

<strong>Помилки hreflang</strong> можуть призвести до показу неправильної мовної версії у результатах пошуку та втрати трафіку з міжнародних ринків."""

    async def analyze(
        self,
        pages: Dict[str, PageData],
        base_url: str,
        **kwargs: Any
    ) -> AnalyzerResult:
        issues: List[AuditIssue] = []
        tables: List[Dict[str, Any]] = []

        # hreflang_map: {page_url: {lang_code: target_url}}
        hreflang_map: Dict[str, Dict[str, str]] = {}
        pages_with_hreflang: Set[str] = set()
        all_languages: Set[str] = set()
        hreflang_entries: List[Dict[str, str]] = []

        # 1. Parse hreflang tags from all pages
        for url, page in pages.items():
            if page.status_code != 200 or not page.html_content:
                continue

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page.html_content, 'lxml')

            page_hreflangs: Dict[str, str] = {}

            for link in soup.find_all('link', rel='alternate'):
                hreflang_attr = link.get('hreflang')
                href_attr = link.get('href')

                if not hreflang_attr or not href_attr:
                    continue

                lang_code = hreflang_attr.strip().lower()
                target_url = href_attr.strip()

                page_hreflangs[lang_code] = target_url
                all_languages.add(lang_code)
                hreflang_entries.append({
                    "source": url,
                    "lang": lang_code,
                    "target": target_url,
                })

            if page_hreflangs:
                hreflang_map[url] = page_hreflangs
                pages_with_hreflang.add(url)

        # 2. If no hreflang tags found — monolingual site, just info
        if not pages_with_hreflang:
            issues.append(self.create_issue(
                category="no_hreflang",
                severity=SeverityLevel.INFO,
                message="Hreflang теги відсутні (одномовний сайт)",
                details="На сторінках сайту не знайдено hreflang тегів. Для одномовного сайту це нормально.",
                recommendation="Якщо сайт має мовні версії, додайте hreflang теги для кожної мовної версії.",
            ))

            severity = self._determine_overall_severity(issues)

            return self.create_result(
                severity=severity,
                summary="Hreflang теги відсутні (одномовний сайт)",
                issues=issues,
                data={
                    "has_hreflang": False,
                    "languages": [],
                    "pages_with_hreflang": 0,
                },
                tables=tables,
            )

        # Hreflang tags found — perform validation
        display_languages = {lang for lang in all_languages if lang != "x-default"}

        issues.append(self.create_issue(
            category="hreflang_found",
            severity=SeverityLevel.SUCCESS,
            message=f"Знайдено {len(display_languages)} мовних версій на {len(pages_with_hreflang)} сторінках",
            details=f"Мови: {', '.join(sorted(display_languages))}",
        ))

        # 3. Check self-referencing
        missing_self_ref: List[str] = []
        for url, langs in hreflang_map.items():
            has_self = False
            for lang_code, target_url in langs.items():
                if target_url.rstrip("/") == url.rstrip("/"):
                    has_self = True
                    break
            if not has_self:
                missing_self_ref.append(url)

        if missing_self_ref:
            issues.append(self.create_issue(
                category="missing_self_reference",
                severity=SeverityLevel.WARNING,
                message=f"Відсутнє самопосилання: {len(missing_self_ref)} сторінок",
                details="Кожна сторінка з hreflang повинна мати тег, що посилається на саму себе.",
                affected_urls=missing_self_ref[:20],
                recommendation="Додайте hreflang тег з посиланням на поточну сторінку для її мовної версії.",
                count=len(missing_self_ref),
            ))

        # 4. Check return (bidirectional) tags
        missing_return_tags: List[str] = []
        for url, langs in hreflang_map.items():
            for lang_code, target_url in langs.items():
                if lang_code == "x-default":
                    continue
                # Normalize target URL for lookup
                target_normalized = target_url.rstrip("/")
                # Find the target page's hreflang map
                target_langs = None
                for map_url, map_langs in hreflang_map.items():
                    if map_url.rstrip("/") == target_normalized:
                        target_langs = map_langs
                        break

                if target_langs is None:
                    # Target page has no hreflang at all
                    missing_return_tags.append(f"{target_url} (з {url})")
                else:
                    # Check if target page points back to source
                    has_return = False
                    for ret_lang, ret_url in target_langs.items():
                        if ret_url.rstrip("/") == url.rstrip("/"):
                            has_return = True
                            break
                    if not has_return:
                        missing_return_tags.append(f"{target_url} (з {url})")

        # Deduplicate
        missing_return_tags = list(dict.fromkeys(missing_return_tags))

        if missing_return_tags:
            issues.append(self.create_issue(
                category="missing_return_tags",
                severity=SeverityLevel.WARNING,
                message=f"Відсутні зворотні посилання: {len(missing_return_tags)}",
                details="Hreflang теги мають бути двосторонніми: якщо сторінка A посилається на B, то B повинна посилатися на A.",
                affected_urls=missing_return_tags[:20],
                recommendation="Додайте відповідні hreflang теги на цільових сторінках, що вказують назад.",
                count=len(missing_return_tags),
            ))

        # 5. Validate language codes
        invalid_codes: Set[str] = set()
        for lang in all_languages:
            # Handle region codes like "uk-UA", "en-US"
            base_lang = lang.split("-")[0] if "-" in lang else lang
            if base_lang not in VALID_LANG_CODES:
                invalid_codes.add(lang)

        if invalid_codes:
            issues.append(self.create_issue(
                category="invalid_lang_codes",
                severity=SeverityLevel.ERROR,
                message=f"Некоректні мовні коди: {', '.join(sorted(invalid_codes))}",
                details="Виявлено мовні коди, що не відповідають стандарту ISO 639-1.",
                recommendation="Використовуйте коректні коди мов за стандартом ISO 639-1 (наприклад: uk, en, de, fr).",
            ))

        # 6. Check x-default presence
        has_x_default = "x-default" in all_languages
        if not has_x_default:
            issues.append(self.create_issue(
                category="missing_x_default",
                severity=SeverityLevel.INFO,
                message="Відсутній x-default hreflang",
                details="x-default вказує версію сторінки для користувачів, мова яких не відповідає жодній із зазначених.",
                recommendation="Додайте hreflang=\"x-default\" з посиланням на основну версію сторінки.",
            ))

        # 7. Build language table
        lang_stats: Dict[str, int] = {}
        for url, langs in hreflang_map.items():
            for lang_code in langs:
                if lang_code not in lang_stats:
                    lang_stats[lang_code] = 0
                lang_stats[lang_code] += 1

        table_rows = []
        for lang_code in sorted(lang_stats.keys()):
            status = "✓ Коректний"
            base_lang = lang_code.split("-")[0] if "-" in lang_code else lang_code
            if base_lang not in VALID_LANG_CODES:
                status = "✗ Некоректний код"
            elif lang_code == "x-default":
                status = "✓ За замовчуванням"

            table_rows.append({
                "Мова": lang_code,
                "Кількість сторінок": str(lang_stats[lang_code]),
                "Статус": status,
            })

        tables.append({
            "title": "Мовні версії",
            "headers": ["Мова", "Кількість сторінок", "Статус"],
            "rows": table_rows[:10],
        })

        # 8. Summary and result
        severity = self._determine_overall_severity(issues)
        summary = f"Знайдено {len(display_languages)} мовних версій на {len(pages_with_hreflang)} сторінках"

        return self.create_result(
            severity=severity,
            summary=summary,
            issues=issues,
            data={
                "has_hreflang": True,
                "languages": sorted(list(all_languages)),
                "pages_with_hreflang": len(pages_with_hreflang),
                "total_entries": len(hreflang_entries),
                "has_x_default": has_x_default,
                "missing_self_references": len(missing_self_ref),
                "missing_return_tags": len(missing_return_tags),
                "invalid_lang_codes": sorted(list(invalid_codes)),
            },
            tables=tables,
        )
