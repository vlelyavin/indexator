"""Mobile friendliness analyzer."""

from typing import Any, Dict, List

from ..models import AnalyzerResult, AuditIssue, PageData, SeverityLevel
from .base import BaseAnalyzer


class MobileAnalyzer(BaseAnalyzer):
    """Analyzer for mobile viewport and friendliness."""

    name = "mobile"
    display_name = "Мобільна адаптивність"
    description = "Перевірка базових вимог до мобільної версії сайту."
    icon = ""
    theory = """<strong>Mobile-First Indexing</strong> — з 2019 року Google індексує мобільну версію сайту як основну. Без коректного viewport мета-тегу сторінка відображатиметься некоректно на мобільних пристроях.

<strong>Вимоги:</strong>
• <strong>Viewport мета-тег</strong> — обов'язковий: <code>&lt;meta name="viewport" content="width=device-width, initial-scale=1"&gt;</code>
• <strong>Без Flash</strong> — Flash не підтримується мобільними браузерами
• <strong>Адаптивний дизайн</strong> — контент повинен масштабуватися під будь-який розмір екрану"""

    async def analyze(
        self,
        pages: Dict[str, PageData],
        base_url: str,
        **kwargs: Any
    ) -> AnalyzerResult:
        issues: List[AuditIssue] = []

        pages_no_viewport: List[str] = []
        pages_bad_viewport: List[str] = []
        pages_with_flash: List[str] = []
        total_ok = 0

        for url, page in pages.items():
            if page.status_code != 200 or not page.html_content:
                continue

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page.html_content, 'lxml')

            # Check for viewport meta tag (case-insensitive name attribute)
            viewport_meta = soup.find('meta', attrs={'name': lambda v: v and v.lower() == 'viewport'})

            has_viewport = False
            has_correct_viewport = False

            if viewport_meta:
                has_viewport = True
                content = viewport_meta.get('content', '')
                if 'width=device-width' in content:
                    has_correct_viewport = True

            if not has_viewport:
                pages_no_viewport.append(url)
            elif not has_correct_viewport:
                pages_bad_viewport.append(url)

            # Detect Flash content
            has_flash = False

            # Check <object> tags
            for obj in soup.find_all('object'):
                obj_type = obj.get('type', '')
                if obj_type == 'application/x-shockwave-flash':
                    has_flash = True
                    break

            # Check <embed> tags
            if not has_flash:
                for embed in soup.find_all('embed'):
                    embed_type = embed.get('type', '')
                    embed_src = embed.get('src', '')
                    if embed_type == 'application/x-shockwave-flash' or embed_src.endswith('.swf'):
                        has_flash = True
                        break

            if has_flash:
                pages_with_flash.append(url)

            # Count pages that are fully OK
            if has_correct_viewport and not has_flash:
                total_ok += 1

        # Create issues
        total_checked = total_ok + len(pages_no_viewport) + len(pages_bad_viewport)

        if not pages_no_viewport and not pages_bad_viewport and total_ok > 0:
            issues.append(self.create_issue(
                category="viewport_ok",
                severity=SeverityLevel.SUCCESS,
                message=f"Всі {total_ok} сторінок мають коректний viewport",
                details="Мета-тег viewport налаштовано правильно на всіх сторінках.",
                count=total_ok,
            ))

        if pages_no_viewport:
            issues.append(self.create_issue(
                category="missing_viewport",
                severity=SeverityLevel.ERROR,
                message=f"{len(pages_no_viewport)} сторінок без viewport",
                details="Без мета-тегу viewport мобільні браузери відображають сторінку у масштабі десктопу.",
                affected_urls=pages_no_viewport[:20],
                recommendation="Додайте <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"> у <head>.",
                count=len(pages_no_viewport),
            ))

        if pages_bad_viewport:
            issues.append(self.create_issue(
                category="bad_viewport",
                severity=SeverityLevel.WARNING,
                message=f"Некоректний viewport: {len(pages_bad_viewport)} сторінок",
                details="Viewport не містить width=device-width, що може спричинити проблеми з масштабуванням.",
                affected_urls=pages_bad_viewport[:20],
                recommendation="Переконайтеся, що viewport містить width=device-width.",
                count=len(pages_bad_viewport),
            ))

        if pages_with_flash:
            issues.append(self.create_issue(
                category="flash_content",
                severity=SeverityLevel.ERROR,
                message=f"Flash-контент: {len(pages_with_flash)} сторінок",
                details="Flash не підтримується мобільними браузерами та більшістю сучасних десктопних браузерів.",
                affected_urls=pages_with_flash[:20],
                recommendation="Замініть Flash-контент на HTML5, CSS3 або JavaScript.",
                count=len(pages_with_flash),
            ))

        # Summary
        if not pages_no_viewport and not pages_bad_viewport and not pages_with_flash:
            summary = f"Всі {total_ok} сторінок мають viewport"
            severity = SeverityLevel.SUCCESS
        else:
            parts = []
            if pages_no_viewport:
                parts.append(f"без viewport: {len(pages_no_viewport)}")
            if pages_bad_viewport:
                parts.append(f"некоректний: {len(pages_bad_viewport)}")
            if pages_with_flash:
                parts.append(f"Flash: {len(pages_with_flash)}")
            summary = f"Проблеми: {', '.join(parts)}"
            severity = self._determine_overall_severity(issues)

        return self.create_result(
            severity=severity,
            summary=summary,
            issues=issues,
            data={
                "total_ok": total_ok,
                "pages_no_viewport": len(pages_no_viewport),
                "pages_bad_viewport": len(pages_bad_viewport),
                "pages_with_flash": len(pages_with_flash),
            },
        )
