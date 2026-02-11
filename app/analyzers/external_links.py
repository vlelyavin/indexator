"""External links analyzer."""

from collections import Counter
from typing import Any, Dict, List
from urllib.parse import urlparse

from ..models import AnalyzerResult, AuditIssue, PageData, SeverityLevel
from .base import BaseAnalyzer


class ExternalLinksAnalyzer(BaseAnalyzer):
    """Analyzer for external outbound links."""

    name = "external_links"
    display_name = "Зовнішні посилання"
    description = "Аналіз вихідних посилань на інші сайти та їх атрибутів."
    icon = ""
    theory = """<strong>Зовнішні посилання (Outbound Links)</strong> — посилання з вашого сайту на інші ресурси.

<strong>Атрибути rel:</strong>
• <strong>Dofollow</strong> — передає PageRank цільовому сайту
• <strong>Nofollow</strong> (<code>rel="nofollow"</code>) — не передає вагу, для реклами
• <strong>Sponsored</strong> (<code>rel="sponsored"</code>) — для платних посилань
• <strong>UGC</strong> (<code>rel="ugc"</code>) — для коментарів користувачів

<strong>Рекомендації:</strong>
• Використовуйте nofollow для комерційних посилань
• Додавайте <code>target="_blank"</code> та <code>rel="noopener"</code> для зовнішніх посилань
• Тримайте баланс між dofollow та nofollow"""

    async def analyze(
        self,
        pages: Dict[str, PageData],
        base_url: str,
        **kwargs: Any
    ) -> AnalyzerResult:
        issues: List[AuditIssue] = []
        tables: List[Dict[str, Any]] = []

        # Collect all external links
        all_external_links = []
        domains_count: Counter = Counter()
        links_without_nofollow = []
        commercial_domains = []

        # Known commercial/affiliate domains that might need nofollow
        commercial_patterns = [
            'amazon.', 'ebay.', 'aliexpress.',
            'booking.com', 'agoda.com', 'hotels.com',
            'click.', 'affiliate.', 'partner.',
            'ad.', 'ads.', 'track.', 'tracking.',
        ]

        for url, page in pages.items():
            if page.status_code != 200:
                continue

            for link in page.external_links:
                href = link.href
                all_external_links.append({
                    'href': href,
                    'source': url,
                    'has_nofollow': link.has_nofollow,
                    'text': link.text,
                })

                # Count domains
                try:
                    domain = urlparse(href).netloc.lower()
                    domains_count[domain] += 1

                    # Check if commercial without nofollow
                    is_commercial = any(pattern in domain for pattern in commercial_patterns)
                    if is_commercial and not link.has_nofollow:
                        commercial_domains.append({
                            'href': href,
                            'source': url,
                            'domain': domain,
                        })

                except Exception:
                    pass

                # Track links without nofollow
                if not link.has_nofollow:
                    links_without_nofollow.append({
                        'href': href,
                        'source': url,
                    })

        total_external = len(all_external_links)
        unique_domains = len(domains_count)

        # Create issues
        if commercial_domains:
            issues.append(self.create_issue(
                category="commercial_no_nofollow",
                severity=SeverityLevel.WARNING,
                message=f"Комерційні посилання без nofollow: {len(commercial_domains)} шт.",
                details="Посилання на комерційні/партнерські сайти рекомендується позначати rel='nofollow' або rel='sponsored'.",
                affected_urls=[link['href'] for link in commercial_domains[:20]],
                recommendation="Додайте rel='nofollow' або rel='sponsored' до комерційних посилань.",
                count=len(commercial_domains),
            ))

        # Check ratio of dofollow links
        dofollow_count = len(links_without_nofollow)
        if total_external > 10 and dofollow_count / total_external > 0.9:
            issues.append(self.create_issue(
                category="many_dofollow",
                severity=SeverityLevel.INFO,
                message=f"Більшість зовнішніх посилань без nofollow ({dofollow_count}/{total_external})",
                details="Велика кількість dofollow посилань передає ваш 'link juice' іншим сайтам.",
                recommendation="Розгляньте додавання nofollow до несуттєвих зовнішніх посилань.",
            ))

        # Check for suspicious/many links to same domain
        for domain, count in domains_count.most_common(5):
            if count > 10:
                issues.append(self.create_issue(
                    category="many_links_same_domain",
                    severity=SeverityLevel.INFO,
                    message=f"Багато посилань на {domain}: {count} шт.",
                    details=f"Знайдено {count} посилань на один домен.",
                    recommendation="Переконайтеся, що це навмисно і посилання релевантні.",
                ))

        # Create table with top domains
        if domains_count:
            top_domains = domains_count.most_common(10)
            table_data = []

            for domain, count in top_domains:
                # Find if most are nofollow
                domain_links = [l for l in all_external_links if domain in l['href']]
                nofollow_count = sum(1 for l in domain_links if l['has_nofollow'])

                table_data.append({
                    "Домен": domain[:50] + "..." if len(domain) > 50 else domain,
                    "Кількість посилань": count,
                    "З nofollow": f"{nofollow_count}/{count}",
                })

            tables.append({
                "title": "Топ-10 доменів за кількістю посилань",
                "headers": ["Домен", "Кількість посилань", "З nofollow"],
                "rows": table_data,
            })

        # Summary
        if not issues:
            summary = f"Знайдено {total_external} зовнішніх посилань на {unique_domains} доменів"
            severity = SeverityLevel.SUCCESS
        else:
            warning_count = sum(1 for i in issues if i.severity == SeverityLevel.WARNING)
            info_count = sum(1 for i in issues if i.severity == SeverityLevel.INFO)
            summary = f"Знайдено {total_external} зовнішніх посилань. Попереджень: {warning_count}, інфо: {info_count}"
            severity = self._determine_overall_severity(issues)

        return self.create_result(
            severity=severity,
            summary=summary,
            issues=issues,
            data={
                "total_external_links": total_external,
                "unique_domains": unique_domains,
                "dofollow_count": dofollow_count,
                "nofollow_count": total_external - dofollow_count,
                "commercial_without_nofollow": len(commercial_domains),
                "top_domains": dict(domains_count.most_common(10)),
            },
            tables=tables,
        )
