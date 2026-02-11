"""Content analyzer."""

from typing import Any, Dict, List

from ..config import settings
from ..models import AnalyzerResult, AuditIssue, PageData, SeverityLevel
from .base import BaseAnalyzer


class ContentAnalyzer(BaseAnalyzer):
    """Analyzer for page content (word count, thin content)."""

    name = "content"
    display_name = "Контент"
    description = "Достатня кількість якісного контенту важлива для ранжування у пошукових системах."
    icon = ""
    theory = """<strong>Контент</strong> — основа SEO. Пошукові системи аналізують текст для розуміння тематики та релевантності сторінки.

<strong>Мінімальні вимоги до об'єму:</strong>
• <strong>Картки товарів:</strong> 300-500 символів — опис, характеристики
• <strong>Категорії:</strong> 1500-2500 символів — SEO-текст з ключовими словами
• <strong>Статті блогу:</strong> 3000-5000+ символів
• <strong>Головна сторінка:</strong> 1000-2000 символів

<strong>Тонкий контент (Thin Content):</strong>
Сторінки з мінімальним або неунікальним текстом можуть не потрапити в індекс або потрапити під фільтр Panda.
• Пишіть унікальний контент з ключовими словами (без переспаму)
• Додавайте корисну інформацію: таблиці, списки, FAQ"""

    async def analyze(
        self,
        pages: Dict[str, PageData],
        base_url: str,
        **kwargs: Any
    ) -> AnalyzerResult:
        issues: List[AuditIssue] = []
        tables: List[Dict[str, Any]] = []

        # Analyze content on each page
        thin_content = []
        empty_pages = []
        word_counts = []

        for url, page in pages.items():
            if page.status_code != 200:
                continue

            word_count = page.word_count
            word_counts.append((url, word_count))

            if word_count == 0:
                empty_pages.append(url)
            elif word_count < settings.MIN_CONTENT_WORDS:
                thin_content.append((url, word_count))

        # Sort by word count (ascending) for thin content
        thin_content.sort(key=lambda x: x[1])
        word_counts.sort(key=lambda x: x[1])

        # Create issues
        if empty_pages:
            issues.append(self.create_issue(
                category="empty_pages",
                severity=SeverityLevel.ERROR,
                message=f"Порожні сторінки: {len(empty_pages)} шт.",
                details="Сторінки без текстового контенту не несуть цінності для пошукових систем.",
                affected_urls=empty_pages[:20],
                recommendation="Додайте унікальний текстовий контент або налаштуйте noindex для цих сторінок.",
                count=len(empty_pages),
            ))

        if thin_content:
            issues.append(self.create_issue(
                category="thin_content",
                severity=SeverityLevel.WARNING,
                message=f"Сторінки з малою кількістю контенту: {len(thin_content)} шт.",
                details=f"Сторінки містять менше {settings.MIN_CONTENT_WORDS} слів. Для категорій та статей рекомендується більше тексту.",
                affected_urls=[url for url, _ in thin_content[:20]],
                recommendation="Розширте контент, додавши корисну інформацію для користувачів.",
                count=len(thin_content),
            ))

        # Create table with thin content pages
        table_data = []

        for url in empty_pages[:5]:
            table_data.append({
                "URL": url[:70] + "..." if len(url) > 70 else url,
                "Кількість слів": 0,
                "Статус": "Порожня",
            })

        for url, count in thin_content[:15]:
            table_data.append({
                "URL": url[:70] + "..." if len(url) > 70 else url,
                "Кількість слів": count,
                "Статус": "Мало контенту",
            })

        if table_data:
            tables.append({
                "title": "Сторінки з недостатнім контентом",
                "headers": ["URL", "Кількість слів", "Статус"],
                "rows": table_data,
            })

        # Calculate statistics
        total_pages = len(word_counts)
        if word_counts:
            total_words = sum(wc for _, wc in word_counts)
            avg_words = total_words // total_pages if total_pages > 0 else 0
            min_words = min(wc for _, wc in word_counts)
            max_words = max(wc for _, wc in word_counts)
        else:
            avg_words = min_words = max_words = 0

        # Summary
        ok_pages = total_pages - len(empty_pages) - len(thin_content)

        if not issues:
            summary = f"Всі {total_pages} сторінок мають достатньо контенту. Середня кількість слів: {avg_words}"
        else:
            parts = []
            if empty_pages:
                parts.append(f"порожніх: {len(empty_pages)}")
            if thin_content:
                parts.append(f"з малим контентом: {len(thin_content)}")
            summary = f"Проблеми з контентом: {', '.join(parts)}. Середня кількість слів: {avg_words}"

        severity = self._determine_overall_severity(issues)

        return self.create_result(
            severity=severity,
            summary=summary,
            issues=issues,
            data={
                "total_pages": total_pages,
                "empty_pages": len(empty_pages),
                "thin_content": len(thin_content),
                "ok_pages": ok_pages,
                "avg_words": avg_words,
                "min_words": min_words,
                "max_words": max_words,
                "min_required": settings.MIN_CONTENT_WORDS,
            },
            tables=tables,
        )
