"""Redirects analyzer."""

from typing import Any, Dict, List

from ..models import AnalyzerResult, AuditIssue, PageData, SeverityLevel
from .base import BaseAnalyzer


class RedirectsAnalyzer(BaseAnalyzer):
    """Analyzer for redirect chains and internal links to redirects."""

    name = "redirects"
    display_name = "Редиректи"
    description = "Аналіз перенаправлень та ланцюжків редиректів на сайті."
    icon = ""
    theory = """<strong>Редиректи</strong> — перенаправлення з однієї URL-адреси на іншу. 301 (постійний) передає ~95% link juice, 302 (тимчасовий) може не передавати.

<strong>Ланцюжки редиректів</strong> — коли URL перенаправляє на іншу URL, яка також перенаправляє далі. Кожен хоп витрачає краулінговий бюджет та додає затримку (~100-500 мс). Google може припинити слідувати після 3+ хопів.

<strong>Як виправити:</strong>
• Замініть ланцюжки на прямий 301 редирект на кінцеву URL
• Оновіть внутрішні посилання, щоб вони вели на кінцеву URL
• Уникайте змішування 301 та 302 в одному ланцюжку"""

    async def analyze(
        self,
        pages: Dict[str, PageData],
        base_url: str,
        **kwargs: Any
    ) -> AnalyzerResult:
        issues: List[AuditIssue] = []
        tables: List[Dict[str, Any]] = []

        # Step 1: Analyze redirect chains
        chains_2_hops: List[Dict[str, Any]] = []  # WARNING: 2 hops
        chains_3_plus: List[Dict[str, Any]] = []  # ERROR: 3+ hops
        all_chains: List[Dict[str, Any]] = []

        # Build a set of URLs that redirect (have redirect_chain with 2+ entries)
        redirecting_urls: Dict[str, str] = {}  # url -> final_url

        for url, page in pages.items():
            if len(page.redirect_chain) >= 2:
                chain_length = len(page.redirect_chain) - 1  # number of hops
                start_url = page.redirect_chain[0]
                end_url = page.redirect_chain[-1]

                redirecting_urls[url] = end_url

                chain_info = {
                    "start_url": start_url,
                    "end_url": end_url,
                    "hops": chain_length,
                    "chain": page.redirect_chain,
                }

                all_chains.append(chain_info)

                if chain_length >= 3:
                    chains_3_plus.append(chain_info)
                elif chain_length == 2:
                    chains_2_hops.append(chain_info)

        # Step 2: Check internal links pointing to redirecting URLs
        internal_links_to_redirects: List[Dict[str, str]] = []

        for url, page in pages.items():
            if page.status_code != 200:
                continue

            for link in page.internal_links:
                if link in redirecting_urls:
                    internal_links_to_redirects.append({
                        "source": url,
                        "target": link,
                        "final_url": redirecting_urls[link],
                    })

        # Step 3: Create issues
        has_issues = False

        if chains_3_plus:
            has_issues = True
            affected = [chain["start_url"] for chain in chains_3_plus]
            issues.append(self.create_issue(
                category="long_redirect_chains",
                severity=SeverityLevel.ERROR,
                message=f"Довгі ланцюжки (3+ хопів): {len(chains_3_plus)}",
                details="Довгі ланцюжки редиректів витрачають краулінговий бюджет. Google може припинити слідувати після 3+ хопів.",
                affected_urls=affected[:20],
                recommendation="Замініть довгі ланцюжки на прямий 301 редирект на кінцеву URL-адресу.",
                count=len(chains_3_plus),
            ))

        if chains_2_hops:
            has_issues = True
            affected = [chain["start_url"] for chain in chains_2_hops]
            issues.append(self.create_issue(
                category="redirect_chains",
                severity=SeverityLevel.WARNING,
                message=f"Ланцюжки редиректів (2 хопи): {len(chains_2_hops)}",
                details="Ланцюжки з двома хопами додають затримку та витрачають краулінговий бюджет.",
                affected_urls=affected[:20],
                recommendation="Скоротіть ланцюжки до одного редиректу, налаштувавши прямий 301 на кінцеву URL.",
                count=len(chains_2_hops),
            ))

        if internal_links_to_redirects:
            has_issues = True
            affected = list(set(item["source"] for item in internal_links_to_redirects))
            issues.append(self.create_issue(
                category="internal_links_to_redirects",
                severity=SeverityLevel.WARNING,
                message=f"Внутрішні посилання на редиректи: {len(internal_links_to_redirects)}",
                details="Внутрішні посилання ведуть на URL, які перенаправляються. Це додає зайву затримку для користувачів та пошукових ботів.",
                affected_urls=affected[:20],
                recommendation="Оновіть внутрішні посилання, замінивши URL з редиректами на кінцеві адреси.",
                count=len(internal_links_to_redirects),
            ))

        if not has_issues:
            issues.append(self.create_issue(
                category="no_redirect_issues",
                severity=SeverityLevel.SUCCESS,
                message="Проблем з редиректами не знайдено",
                details="На сайті не виявлено проблемних ланцюжків редиректів.",
                recommendation="Продовжуйте стежити за тим, щоб внутрішні посилання вели на кінцеві URL-адреси.",
            ))

        # Step 4: Create table
        table_data = []

        # Sort chains by hops descending
        all_chains.sort(key=lambda x: x["hops"], reverse=True)

        for chain in all_chains[:10]:
            table_data.append({
                "Початковий URL": chain["start_url"][:70] + "..." if len(chain["start_url"]) > 70 else chain["start_url"],
                "Кінцевий URL": chain["end_url"][:70] + "..." if len(chain["end_url"]) > 70 else chain["end_url"],
                "Хопів": chain["hops"],
            })

        if table_data:
            tables.append({
                "title": "Ланцюжки редиректів",
                "headers": ["Початковий URL", "Кінцевий URL", "Хопів"],
                "rows": table_data,
            })

        # Step 5: Summary
        total_chains = len(chains_2_hops) + len(chains_3_plus)
        if total_chains > 0:
            summary = f"Знайдено {total_chains} ланцюжків редиректів"
        else:
            summary = "Проблем з редиректами не знайдено"

        severity = self._determine_overall_severity(issues)

        return self.create_result(
            severity=severity,
            summary=summary,
            issues=issues,
            data={
                "total_redirects": len(all_chains),
                "chains_2_hops": len(chains_2_hops),
                "chains_3_plus": len(chains_3_plus),
                "internal_links_to_redirects": len(internal_links_to_redirects),
            },
            tables=tables,
        )
