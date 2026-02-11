"""Social meta tags (Open Graph & Twitter Cards) analyzer."""

from typing import Any, Dict, List

from bs4 import BeautifulSoup

from ..models import AnalyzerResult, AuditIssue, PageData, SeverityLevel
from .base import BaseAnalyzer


class SocialTagsAnalyzer(BaseAnalyzer):
    """Analyzer for Open Graph and Twitter Card meta tags."""

    name = "social_tags"
    display_name = "Соціальні мета-теги"
    description = "Аналіз Open Graph та Twitter Card тегів для коректного відображення у соціальних мережах."
    icon = ""
    theory = """<strong>Open Graph (OG)</strong> — протокол розмітки, що контролює відображення сторінки при поширенні у Facebook, LinkedIn, Telegram та інших платформах.

<strong>Основні OG теги:</strong>
• <strong>og:title</strong> — заголовок для соцмереж (до 60 символів)
• <strong>og:description</strong> — опис (до 200 символів)
• <strong>og:image</strong> — зображення для прев'ю (рекомендовано 1200x630 px)
• <strong>og:url</strong> — канонічна URL сторінки
• <strong>og:type</strong> — тип контенту (website, article)

<strong>Twitter Cards:</strong>
• <strong>twitter:card</strong> — тип картки (summary, summary_large_image)
• <strong>twitter:title</strong>, <strong>twitter:description</strong>, <strong>twitter:image</strong>

<strong>Переваги:</strong> привабливі прев'ю при поширенні, збільшення переходів із соцмереж, контроль над зовнішнім виглядом посилань."""

    async def analyze(
        self,
        pages: Dict[str, PageData],
        base_url: str,
        **kwargs: Any
    ) -> AnalyzerResult:
        issues: List[AuditIssue] = []
        tables: List[Dict[str, Any]] = []

        pages_with_og: List[str] = []
        pages_without_og: List[str] = []
        pages_with_og_image: List[str] = []
        pages_without_og_image: List[str] = []
        pages_with_og_description: List[str] = []
        pages_without_og_description: List[str] = []
        pages_with_twitter: List[str] = []
        pages_without_twitter: List[str] = []

        total_pages = 0
        page_tag_status: List[Dict[str, str]] = []

        for url, page in pages.items():
            if page.status_code != 200 or not page.html_content:
                continue

            total_pages += 1
            soup = BeautifulSoup(page.html_content, 'lxml')

            # Check Open Graph tags
            og_title = soup.find('meta', attrs={'property': 'og:title'})
            og_description = soup.find('meta', attrs={'property': 'og:description'})
            og_image = soup.find('meta', attrs={'property': 'og:image'})
            og_url = soup.find('meta', attrs={'property': 'og:url'})
            og_type = soup.find('meta', attrs={'property': 'og:type'})

            has_og = bool(og_title)
            has_og_image = bool(og_image and og_image.get('content', '').strip())
            has_og_desc = bool(og_description and og_description.get('content', '').strip())

            # Check Twitter Card tags
            twitter_card = soup.find('meta', attrs={'name': 'twitter:card'})
            twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
            twitter_description = soup.find('meta', attrs={'name': 'twitter:description'})
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})

            has_twitter = bool(twitter_card)

            # Track pages
            if has_og:
                pages_with_og.append(url)
            else:
                pages_without_og.append(url)

            if has_og_image:
                pages_with_og_image.append(url)
            elif has_og:
                pages_without_og_image.append(url)

            if has_og_desc:
                pages_with_og_description.append(url)
            elif has_og:
                pages_without_og_description.append(url)

            if has_twitter:
                pages_with_twitter.append(url)
            else:
                pages_without_twitter.append(url)

            # Collect table data
            page_tag_status.append({
                "URL": url,
                "og:title": "\u2713" if has_og else "\u2717",
                "og:image": "\u2713" if has_og_image else "\u2717",
                "twitter:card": "\u2713" if has_twitter else "\u2717",
            })

        # Create issues
        if total_pages > 0 and len(pages_with_og) == total_pages:
            issues.append(self.create_issue(
                category="og_tags_ok",
                severity=SeverityLevel.SUCCESS,
                message=f"Open Graph теги присутні на всіх {total_pages} сторінках",
                details="Всі сторінки мають коректні OG теги для відображення у соціальних мережах.",
                recommendation="Продовжуйте підтримувати OG теги актуальними.",
                count=total_pages,
            ))
        elif pages_without_og:
            issues.append(self.create_issue(
                category="missing_og_tags",
                severity=SeverityLevel.WARNING,
                message=f"Open Graph теги відсутні на {len(pages_without_og)} сторінках",
                details="Сторінки без OG тегів відображатимуться некоректно при поширенні у соціальних мережах.",
                affected_urls=pages_without_og[:20],
                recommendation="Додайте мета-теги og:title, og:description та og:image на всі сторінки.",
                count=len(pages_without_og),
            ))

        if pages_without_og_image:
            issues.append(self.create_issue(
                category="missing_og_image",
                severity=SeverityLevel.WARNING,
                message=f"Відсутній og:image на {len(pages_without_og_image)} сторінках",
                details="Без og:image соціальні мережі можуть обрати випадкове зображення або не показати прев'ю.",
                affected_urls=pages_without_og_image[:20],
                recommendation="Додайте og:image з розміром 1200x630 px для кожної сторінки.",
                count=len(pages_without_og_image),
            ))

        if pages_without_og_description:
            issues.append(self.create_issue(
                category="missing_og_description",
                severity=SeverityLevel.INFO,
                message=f"Відсутній og:description на {len(pages_without_og_description)} сторінках",
                details="Без og:description соціальні мережі використовуватимуть звичайний meta description або фрагмент тексту.",
                affected_urls=pages_without_og_description[:20],
                recommendation="Додайте og:description з коротким привабливим описом сторінки (до 200 символів).",
                count=len(pages_without_og_description),
            ))

        if pages_without_twitter:
            issues.append(self.create_issue(
                category="missing_twitter_card",
                severity=SeverityLevel.INFO,
                message=f"Twitter Card теги відсутні на {len(pages_without_twitter)} сторінках",
                details="Без twitter:card посилання в Twitter/X відображатимуться без розширеного прев'ю.",
                affected_urls=pages_without_twitter[:20],
                recommendation="Додайте <meta name=\"twitter:card\" content=\"summary_large_image\"> для розширених прев'ю.",
                count=len(pages_without_twitter),
            ))

        # Create table with tag status per page
        if page_tag_status:
            tables.append({
                "title": "Статус соціальних тегів",
                "headers": ["URL", "og:title", "og:image", "twitter:card"],
                "rows": page_tag_status[:10],
            })

        # Summary
        num_og = len(pages_with_og)
        num_twitter = len(pages_with_twitter)

        if total_pages == 0:
            summary = "Немає сторінок для аналізу"
        elif pages_without_og or pages_without_twitter:
            missing_count = len(pages_without_og) + len(pages_without_twitter)
            summary = f"OG теги: {num_og}/{total_pages} сторінок. Twitter Cards: {num_twitter}/{total_pages}"
        else:
            summary = f"OG теги: {num_og}/{total_pages} сторінок. Twitter Cards: {num_twitter}/{total_pages}"

        severity = self._determine_overall_severity(issues)

        return self.create_result(
            severity=severity,
            summary=summary,
            issues=issues,
            data={
                "total_pages": total_pages,
                "pages_with_og": len(pages_with_og),
                "pages_without_og": len(pages_without_og),
                "pages_with_og_image": len(pages_with_og_image),
                "pages_without_og_image": len(pages_without_og_image),
                "pages_with_twitter": len(pages_with_twitter),
                "pages_without_twitter": len(pages_without_twitter),
            },
            tables=tables,
        )
