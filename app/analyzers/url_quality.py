"""URL quality analyzer."""

from typing import Any, Dict, List
from urllib.parse import urlparse

from ..models import AnalyzerResult, AuditIssue, PageData, SeverityLevel
from .base import BaseAnalyzer


class URLQualityAnalyzer(BaseAnalyzer):
    """Analyzer for URL structure and quality."""

    name = "url_quality"
    display_name = "Якість URL"
    description = "Аналіз структури та якості URL-адрес сторінок сайту."
    icon = ""
    theory = """<strong>SEO-дружні URL</strong> — важливий фактор ранжування та юзабіліті. Пошукові системи краще розуміють структуровані URL з ключовими словами.

<strong>Вимоги до URL:</strong>
• <strong>Короткі</strong> — до 75 символів (шлях), критично — понад 120
• <strong>Читабельні</strong> — зрозумілі людині та пошуковим роботам
• <strong>Дефіси</strong> — замість підкреслень для розділення слів
• <strong>Нижній регістр</strong> — уникайте великих літер (можуть створювати дублі)
• <strong>Без спецсимволів</strong> — тільки латиниця, цифри та дефіси
• <strong>Ключові слова в URL</strong> — допоміжний сигнал релевантності для Google"""

    async def analyze(
        self,
        pages: Dict[str, PageData],
        base_url: str,
        **kwargs: Any
    ) -> AnalyzerResult:
        issues: List[AuditIssue] = []
        tables: List[Dict[str, Any]] = []

        long_urls_warn: List[str] = []
        long_urls_error: List[str] = []
        uppercase_urls: List[str] = []
        special_chars_urls: List[str] = []
        underscore_urls: List[str] = []
        dynamic_urls: List[str] = []
        double_slash_urls: List[str] = []

        # Collect table data for problematic URLs
        table_data: List[Dict[str, str]] = []

        for url, page in pages.items():
            if page.status_code != 200:
                continue

            parsed = urlparse(url)
            path = parsed.path
            path_length = len(path)
            problems: List[str] = []

            # Check path length
            if path_length > 120:
                long_urls_error.append(url)
                problems.append("Занадто довгий URL")
            elif path_length > 75:
                long_urls_warn.append(url)
                problems.append("Довгий URL")

            # Check uppercase
            if any(c.isupper() for c in path):
                uppercase_urls.append(url)
                problems.append("Великі літери")

            # Check non-ASCII characters
            if any(ord(c) > 127 for c in path):
                special_chars_urls.append(url)
                problems.append("Спецсимволи")

            # Check underscores
            if '_' in path:
                underscore_urls.append(url)
                problems.append("Підкреслення")

            # Check dynamic parameters (more than 1 param)
            if parsed.query and len(parsed.query.split('&')) > 1:
                dynamic_urls.append(url)
                problems.append("Параметри")

            # Check double slashes in path
            if '//' in path:
                double_slash_urls.append(url)
                problems.append("Подвійні слеші")

            if problems:
                table_data.append({
                    "URL": url,
                    "Проблема": ", ".join(problems),
                    "Довжина": str(path_length),
                })

        # Create issues
        if long_urls_warn:
            issues.append(self.create_issue(
                category="long_urls",
                severity=SeverityLevel.WARNING,
                message=f"Довгі URL: {len(long_urls_warn)} сторінок",
                details="URL з довжиною шляху понад 75 символів гірше сприймаються користувачами та пошуковими системами.",
                affected_urls=long_urls_warn[:20],
                recommendation="Скоротіть URL, використовуючи лише ключові слова.",
                count=len(long_urls_warn),
            ))

        if long_urls_error:
            issues.append(self.create_issue(
                category="long_urls",
                severity=SeverityLevel.ERROR,
                message=f"Занадто довгі URL: {len(long_urls_error)} сторінок",
                details="URL з довжиною шляху понад 120 символів можуть обрізатися у пошуковій видачі.",
                affected_urls=long_urls_error[:20],
                recommendation="Терміново скоротіть URL до 75 символів.",
                count=len(long_urls_error),
            ))

        if uppercase_urls:
            issues.append(self.create_issue(
                category="uppercase_urls",
                severity=SeverityLevel.WARNING,
                message=f"URL з великими літерами: {len(uppercase_urls)}",
                details="URL з великими літерами можуть створювати дублі сторінок, оскільки сервер може обробляти різний регістр як різні сторінки.",
                affected_urls=uppercase_urls[:20],
                recommendation="Використовуйте тільки нижній регістр в URL та налаштуйте 301-редирект.",
                count=len(uppercase_urls),
            ))

        if special_chars_urls:
            issues.append(self.create_issue(
                category="special_chars",
                severity=SeverityLevel.WARNING,
                message=f"URL зі спецсимволами: {len(special_chars_urls)}",
                details="Non-ASCII символи в URL кодуються у відсотковий формат, що ускладнює читання.",
                affected_urls=special_chars_urls[:20],
                recommendation="Використовуйте тільки латиницю, цифри та дефіси в URL.",
                count=len(special_chars_urls),
            ))

        if underscore_urls:
            issues.append(self.create_issue(
                category="underscores",
                severity=SeverityLevel.INFO,
                message=f"URL з підкресленнями: {len(underscore_urls)}",
                details="Google рекомендує використовувати дефіси замість підкреслень для розділення слів у URL.",
                affected_urls=underscore_urls[:20],
                recommendation="Замініть підкреслення на дефіси та налаштуйте 301-редирект.",
                count=len(underscore_urls),
            ))

        if dynamic_urls:
            issues.append(self.create_issue(
                category="dynamic_params",
                severity=SeverityLevel.INFO,
                message=f"URL з параметрами: {len(dynamic_urls)}",
                details="URL з кількома GET-параметрами виглядають менш привабливо та можуть створювати дублі.",
                affected_urls=dynamic_urls[:20],
                recommendation="Використовуйте ЧПУ (людинозрозумілі URL) замість динамічних параметрів.",
                count=len(dynamic_urls),
            ))

        if double_slash_urls:
            issues.append(self.create_issue(
                category="double_slashes",
                severity=SeverityLevel.ERROR,
                message=f"Подвійні слеші в URL: {len(double_slash_urls)}",
                details="Подвійні слеші в шляху URL створюють дублі сторінок та ускладнюють індексацію.",
                affected_urls=double_slash_urls[:20],
                recommendation="Виправте подвійні слеші та налаштуйте 301-редирект на коректний URL.",
                count=len(double_slash_urls),
            ))

        # If no problems found
        has_problems = (long_urls_warn or long_urls_error or uppercase_urls or
                        special_chars_urls or underscore_urls or dynamic_urls or double_slash_urls)

        if not has_problems:
            issues.append(self.create_issue(
                category="urls_ok",
                severity=SeverityLevel.SUCCESS,
                message="Всі URL відповідають стандартам",
                details="Структура URL-адрес сайту відповідає рекомендаціям SEO.",
            ))

        # Create table with problematic URLs
        if table_data:
            tables.append({
                "title": "Проблемні URL",
                "headers": ["URL", "Проблема", "Довжина"],
                "rows": table_data[:10],
            })

        # Summary
        total_pages = len([p for p in pages.values() if p.status_code == 200])

        if not has_problems:
            summary = "Всі URL якісні"
            severity = SeverityLevel.SUCCESS
        else:
            parts = []
            if long_urls_warn or long_urls_error:
                parts.append(f"довгі: {len(long_urls_warn) + len(long_urls_error)}")
            if uppercase_urls:
                parts.append(f"великі літери: {len(uppercase_urls)}")
            if special_chars_urls:
                parts.append(f"спецсимволи: {len(special_chars_urls)}")
            if underscore_urls:
                parts.append(f"підкреслення: {len(underscore_urls)}")
            if dynamic_urls:
                parts.append(f"параметри: {len(dynamic_urls)}")
            if double_slash_urls:
                parts.append(f"подвійні слеші: {len(double_slash_urls)}")
            summary = f"Знайдено проблем: {', '.join(parts)}"
            severity = self._determine_overall_severity(issues)

        return self.create_result(
            severity=severity,
            summary=summary,
            issues=issues,
            data={
                "total_pages": total_pages,
                "long_urls_warn": len(long_urls_warn),
                "long_urls_error": len(long_urls_error),
                "uppercase_urls": len(uppercase_urls),
                "special_chars_urls": len(special_chars_urls),
                "underscore_urls": len(underscore_urls),
                "dynamic_urls": len(dynamic_urls),
                "double_slash_urls": len(double_slash_urls),
            },
            tables=tables,
        )
