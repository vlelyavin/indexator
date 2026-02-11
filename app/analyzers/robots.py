"""Robots and indexing analyzer."""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from ..crawler import fetch_url_content
from ..models import AnalyzerResult, AuditIssue, PageData, RobotsTxtData, SitemapData, SeverityLevel
from .base import BaseAnalyzer


class RobotsAnalyzer(BaseAnalyzer):
    """Analyzer for robots.txt, sitemap.xml, and indexing issues."""

    name = "robots"
    display_name = "Індексація"
    description = "Правильне налаштування robots.txt та sitemap.xml допомагає пошуковим системам ефективно індексувати сайт."
    icon = ""
    theory = """<strong>Robots.txt</strong> — файл, що керує доступом пошукових роботів до сторінок сайту.

<strong>Основні директиви:</strong>
• <code>User-agent: *</code> — правила для всіх роботів
• <code>Disallow: /admin/</code> — заборона індексації шляху
• <code>Allow: /</code> — дозвіл індексації
• <code>Sitemap: URL</code> — посилання на карту сайту

<strong>Sitemap.xml</strong> — список сторінок для індексації. Допомагає роботам знайти всі сторінки та прискорює індексацію нового контенту.

<strong>Рекомендації:</strong>
• Завжди майте robots.txt та sitemap.xml
• Вкажіть sitemap у robots.txt
• Не блокуйте CSS/JS файли
• Подайте sitemap у Google Search Console"""

    async def analyze(
        self,
        pages: Dict[str, PageData],
        base_url: str,
        **kwargs: Any
    ) -> AnalyzerResult:
        issues: List[AuditIssue] = []
        tables: List[Dict[str, Any]] = []

        # Check robots.txt
        robots_url = urljoin(base_url, "/robots.txt")
        robots_data = await self._analyze_robots_txt(robots_url)

        # Check sitemap.xml (support for multiple sitemaps and sitemap index)
        sitemap_urls_to_check = robots_data.sitemaps if robots_data.sitemaps else [urljoin(base_url, "/sitemap.xml")]
        sitemap_data, sitemap_urls_set, sitemap_lastmod = await self._analyze_all_sitemaps(sitemap_urls_to_check, base_url)

        # Check noindex pages
        noindex_pages = []
        canonical_issues = []

        for url, page in pages.items():
            if page.status_code != 200:
                continue

            # Check noindex
            if page.has_noindex:
                noindex_pages.append(url)

            # Check canonical
            if page.canonical:
                # Canonical should point to a valid URL
                if page.canonical != url:
                    # Different canonical - could be intentional
                    if page.canonical not in pages:
                        canonical_issues.append({
                            'url': url,
                            'canonical': page.canonical,
                            'issue': 'Canonical вказує на сторінку поза сайтом або неіснуючу',
                        })

        # Create issues for robots.txt
        if not robots_data.exists:
            issues.append(self.create_issue(
                category="no_robots_txt",
                severity=SeverityLevel.WARNING,
                message="Файл robots.txt відсутній",
                details="robots.txt допомагає контролювати, які сторінки індексуються пошуковими системами.",
                recommendation="Створіть файл robots.txt у корені сайту.",
            ))
        else:
            if robots_data.errors:
                issues.append(self.create_issue(
                    category="robots_txt_errors",
                    severity=SeverityLevel.WARNING,
                    message=f"Помилки у robots.txt: {len(robots_data.errors)} шт.",
                    details="; ".join(robots_data.errors[:5]),
                    recommendation="Виправте синтаксичні помилки у robots.txt.",
                    count=len(robots_data.errors),
                ))

            if not robots_data.sitemaps:
                issues.append(self.create_issue(
                    category="no_sitemap_in_robots",
                    severity=SeverityLevel.INFO,
                    message="Sitemap не вказано у robots.txt",
                    details="Рекомендується вказати шлях до sitemap у robots.txt.",
                    recommendation="Додайте рядок 'Sitemap: https://yoursite.com/sitemap.xml' у robots.txt.",
                ))

        # Create issues for sitemap
        if not sitemap_data.exists:
            issues.append(self.create_issue(
                category="no_sitemap",
                severity=SeverityLevel.ERROR,
                message="Файл sitemap.xml відсутній",
                details="Sitemap допомагає пошуковим системам знаходити всі сторінки сайту.",
                recommendation="Створіть sitemap.xml та додайте його у robots.txt та Google Search Console.",
            ))
        else:
            if sitemap_data.errors:
                issues.append(self.create_issue(
                    category="sitemap_errors",
                    severity=SeverityLevel.WARNING,
                    message=f"Проблеми з sitemap: {len(sitemap_data.errors)} шт.",
                    details="; ".join(sitemap_data.errors[:5]),
                    recommendation="Перевірте валідність sitemap.xml.",
                    count=len(sitemap_data.errors),
                ))

            if sitemap_data.urls_count == 0:
                issues.append(self.create_issue(
                    category="empty_sitemap",
                    severity=SeverityLevel.WARNING,
                    message="Sitemap порожній",
                    details="Sitemap не містить URL-адрес.",
                    recommendation="Додайте URL-адреси сторінок у sitemap.xml.",
                ))

            # Compare sitemap URLs with crawled pages
            if sitemap_urls_set:
                crawled_urls = set(url for url, page in pages.items() if page.status_code == 200)

                # URLs in sitemap but not found/crawled
                sitemap_not_crawled = sitemap_urls_set - crawled_urls
                # Filter to same domain only
                base_domain = urlparse(base_url).netloc
                sitemap_not_crawled = {url for url in sitemap_not_crawled if urlparse(url).netloc == base_domain}

                # URLs crawled but not in sitemap
                crawled_not_in_sitemap = crawled_urls - sitemap_urls_set
                # Filter to same domain only
                crawled_not_in_sitemap = {url for url in crawled_not_in_sitemap if urlparse(url).netloc == base_domain}

                if sitemap_not_crawled:
                    issues.append(self.create_issue(
                        category="sitemap_urls_not_found",
                        severity=SeverityLevel.WARNING,
                        message=f"URL у sitemap не знайдено на сайті: {len(sitemap_not_crawled)} шт.",
                        details="Ці URL вказані в sitemap, але не були знайдені краулером або повертають помилку.",
                        affected_urls=list(sitemap_not_crawled)[:20],
                        recommendation="Перевірте ці URL та видаліть неіснуючі з sitemap.",
                        count=len(sitemap_not_crawled),
                    ))

                if crawled_not_in_sitemap and len(crawled_not_in_sitemap) > 5:
                    issues.append(self.create_issue(
                        category="pages_not_in_sitemap",
                        severity=SeverityLevel.INFO,
                        message=f"Сторінки не включені в sitemap: {len(crawled_not_in_sitemap)} шт.",
                        details="Ці сторінки знайдені на сайті, але відсутні в sitemap.xml.",
                        affected_urls=list(crawled_not_in_sitemap)[:20],
                        recommendation="Додайте важливі сторінки в sitemap для кращої індексації.",
                        count=len(crawled_not_in_sitemap),
                    ))

            # Check lastmod dates
            if sitemap_lastmod:
                old_lastmod = []
                six_months_ago = datetime.now() - timedelta(days=180)

                for url, lastmod_str in sitemap_lastmod.items():
                    try:
                        # Parse various date formats
                        lastmod_date = None
                        for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S']:
                            try:
                                lastmod_date = datetime.strptime(lastmod_str[:19], fmt[:len(lastmod_str[:19])])
                                break
                            except ValueError:
                                continue

                        if lastmod_date and lastmod_date < six_months_ago:
                            old_lastmod.append((url, lastmod_str))
                    except Exception:
                        pass

                if old_lastmod and len(old_lastmod) > len(sitemap_lastmod) * 0.5:
                    issues.append(self.create_issue(
                        category="sitemap_old_lastmod",
                        severity=SeverityLevel.INFO,
                        message=f"Застарілі дати lastmod у sitemap: {len(old_lastmod)} URL",
                        details="Більше половини URL мають lastmod старше 6 місяців. Оновіть дати або контент.",
                        affected_urls=[url for url, _ in old_lastmod[:10]],
                        recommendation="Оновіть lastmod дати в sitemap при зміні контенту сторінок.",
                    ))

        # Create issues for noindex pages
        if noindex_pages:
            issues.append(self.create_issue(
                category="noindex_pages",
                severity=SeverityLevel.INFO,
                message=f"Сторінки з noindex: {len(noindex_pages)} шт.",
                details="Ці сторінки не будуть індексуватися пошуковими системами.",
                affected_urls=noindex_pages[:20],
                recommendation="Переконайтеся, що noindex встановлено навмисно для цих сторінок.",
                count=len(noindex_pages),
            ))

        # Create issues for canonical
        if canonical_issues:
            issues.append(self.create_issue(
                category="canonical_issues",
                severity=SeverityLevel.WARNING,
                message=f"Проблеми з canonical: {len(canonical_issues)} шт.",
                details="Canonical теги вказують на сторінки, які не існують або знаходяться поза сайтом.",
                affected_urls=[c['url'] for c in canonical_issues[:20]],
                recommendation="Перевірте та виправте canonical теги.",
                count=len(canonical_issues),
            ))

        # Create table with indexing status
        table_data = []

        table_data.append({
            "Елемент": "robots.txt",
            "Статус": "✓ Є" if robots_data.exists else "✗ Відсутній",
            "Деталі": f"Sitemap: {len(robots_data.sitemaps)}, Disallow: {len(robots_data.disallowed_paths)}" if robots_data.exists else "-",
        })

        table_data.append({
            "Елемент": "sitemap.xml",
            "Статус": "✓ Є" if sitemap_data.exists else "✗ Відсутній",
            "Деталі": f"URL: {sitemap_data.urls_count}, файлів: {sitemap_data.sitemap_count}" if sitemap_data.exists else "-",
        })

        table_data.append({
            "Елемент": "noindex сторінки",
            "Статус": f"{len(noindex_pages)} шт." if noindex_pages else "0",
            "Деталі": noindex_pages[0][:50] + "..." if noindex_pages else "Немає",
        })

        tables.append({
            "title": "Статус індексації",
            "headers": ["Елемент", "Статус", "Деталі"],
            "rows": table_data,
        })

        # Summary
        if not issues:
            summary = "Налаштування індексації в порядку"
        else:
            error_count = sum(1 for i in issues if i.severity == SeverityLevel.ERROR)
            warning_count = sum(1 for i in issues if i.severity == SeverityLevel.WARNING)
            parts = []
            if error_count:
                parts.append(f"помилок: {error_count}")
            if warning_count:
                parts.append(f"попереджень: {warning_count}")
            summary = f"Проблеми з індексацією: {', '.join(parts)}"

        severity = self._determine_overall_severity(issues)

        # Calculate sitemap comparison stats
        crawled_urls = set(url for url, page in pages.items() if page.status_code == 200)
        base_domain = urlparse(base_url).netloc
        sitemap_not_crawled_count = len({url for url in sitemap_urls_set - crawled_urls if urlparse(url).netloc == base_domain}) if sitemap_urls_set else 0
        crawled_not_in_sitemap_count = len({url for url in crawled_urls - sitemap_urls_set if urlparse(url).netloc == base_domain}) if sitemap_urls_set else 0

        return self.create_result(
            severity=severity,
            summary=summary,
            issues=issues,
            data={
                "robots_txt": robots_data.model_dump(),
                "sitemap": sitemap_data.model_dump(),
                "noindex_pages": len(noindex_pages),
                "canonical_issues": len(canonical_issues),
                "sitemap_urls_count": len(sitemap_urls_set),
                "sitemap_not_crawled": sitemap_not_crawled_count,
                "crawled_not_in_sitemap": crawled_not_in_sitemap_count,
            },
            tables=tables,
        )

    async def _analyze_robots_txt(self, url: str) -> RobotsTxtData:
        """Analyze robots.txt file."""
        status, content = await fetch_url_content(url)

        if status != 200 or not content:
            return RobotsTxtData(exists=False)

        sitemaps = []
        disallowed = []
        errors = []

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse directives
            if ':' in line:
                directive, _, value = line.partition(':')
                directive = directive.strip().lower()
                value = value.strip()

                if directive == 'sitemap':
                    sitemaps.append(value)
                elif directive == 'disallow':
                    if value:
                        disallowed.append(value)
                elif directive not in ['user-agent', 'allow', 'crawl-delay', 'host']:
                    errors.append(f"Рядок {i}: невідома директива '{directive}'")
            else:
                if line and not line.startswith('#'):
                    errors.append(f"Рядок {i}: неправильний синтаксис")

        return RobotsTxtData(
            exists=True,
            content=content,
            sitemaps=sitemaps,
            disallowed_paths=disallowed,
            errors=errors[:10],
        )

    async def _analyze_all_sitemaps(
        self,
        sitemap_urls: List[str],
        base_url: str
    ) -> Tuple[SitemapData, Set[str], Dict[str, str]]:
        """
        Analyze all sitemaps including sitemap index files.

        Returns:
            Tuple of (SitemapData, set of all URLs, dict of URL -> lastmod)
        """
        all_urls: Set[str] = set()
        all_lastmod: Dict[str, str] = {}
        all_errors: List[str] = []
        sitemap_count = 0
        total_urls = 0
        exists = False

        async def parse_sitemap(url: str, depth: int = 0) -> None:
            nonlocal sitemap_count, total_urls, exists

            if depth > 2:  # Prevent infinite recursion
                return

            status, content = await fetch_url_content(url)

            if status != 200 or not content:
                if depth == 0:
                    all_errors.append(f"Не вдалося завантажити: {url}")
                return

            exists = True
            sitemap_count += 1

            try:
                # Check if this is a sitemap index
                if '<sitemapindex' in content:
                    # Extract sitemap URLs from index
                    loc_matches = re.findall(r'<loc>([^<]+)</loc>', content)
                    for sitemap_url in loc_matches[:50]:  # Limit to 50 sitemaps
                        await parse_sitemap(sitemap_url.strip(), depth + 1)
                else:
                    # Regular sitemap - extract URLs and lastmod
                    # Parse URL entries
                    url_entries = re.findall(
                        r'<url>\s*<loc>([^<]+)</loc>(?:\s*<lastmod>([^<]*)</lastmod>)?',
                        content,
                        re.DOTALL
                    )

                    for loc, lastmod in url_entries:
                        loc = loc.strip()
                        all_urls.add(loc)
                        total_urls += 1
                        if lastmod:
                            all_lastmod[loc] = lastmod.strip()

                    # Also count URLs that might have different ordering
                    if not url_entries:
                        loc_matches = re.findall(r'<loc>([^<]+)</loc>', content)
                        for loc in loc_matches:
                            loc = loc.strip()
                            all_urls.add(loc)
                            total_urls += 1

            except Exception as e:
                all_errors.append(f"Помилка парсингу {url}: {str(e)}")

        # Process all sitemap URLs
        for sitemap_url in sitemap_urls[:10]:  # Limit to 10 sitemaps from robots.txt
            await parse_sitemap(sitemap_url)

        sitemap_data = SitemapData(
            exists=exists,
            url=sitemap_urls[0] if sitemap_urls else "",
            urls_count=total_urls,
            errors=all_errors[:10],
            sitemap_count=sitemap_count,
        )

        return sitemap_data, all_urls, all_lastmod
