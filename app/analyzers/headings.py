"""Headings (H1-H6) analyzer."""

from collections import Counter
from typing import Any, Dict, List

from ..models import AnalyzerResult, AuditIssue, PageData, SeverityLevel
from .base import BaseAnalyzer


class HeadingsAnalyzer(BaseAnalyzer):
    """Analyzer for H1-H6 headings hierarchy."""

    name = "headings"
    display_name = "Заголовки H1-H6"
    description = "Аналіз заголовків H1-H6: наявність, унікальність та правильна ієрархія."
    icon = ""
    theory = """<strong>Заголовки H1-H6</strong> — ієрархія заголовків для структурування контенту сторінки.

<strong>Правила:</strong>
• <strong>Рівно один H1</strong> на сторінку (кілька — розмивають фокус)
• H1 унікальний для кожної сторінки, 20-70 символів
• <strong>Ієрархія H1 → H2 → H3</strong> — не пропускайте рівні (H1 → H3 без H2 — порушення)
• H2 використовуйте для основних розділів, H3 для підрозділів"""

    async def analyze(
        self,
        pages: Dict[str, PageData],
        base_url: str,
        **kwargs: Any
    ) -> AnalyzerResult:
        issues: List[AuditIssue] = []
        tables: List[Dict[str, Any]] = []

        # Collect H1 data
        all_h1s = {}
        missing_h1 = []
        multiple_h1 = []
        empty_h1 = []

        for url, page in pages.items():
            if page.status_code != 200:
                continue

            h1_tags = page.h1_tags

            if not h1_tags:
                missing_h1.append(url)
            elif len(h1_tags) > 1:
                multiple_h1.append((url, h1_tags))
                all_h1s[url] = h1_tags[0]  # Take first for duplicate check
            else:
                h1_text = h1_tags[0].strip()
                if not h1_text:
                    empty_h1.append(url)
                else:
                    all_h1s[url] = h1_text

        # Find duplicate H1s
        h1_counts = Counter(all_h1s.values())
        duplicate_h1s = {h1: count for h1, count in h1_counts.items() if count > 1}

        # Create issues
        if missing_h1:
            issues.append(self.create_issue(
                category="missing_h1",
                severity=SeverityLevel.ERROR,
                message=f"Відсутній H1: {len(missing_h1)} сторінок",
                details="Заголовок H1 допомагає пошуковим системам зрозуміти тему сторінки.",
                affected_urls=missing_h1[:20],
                recommendation="Додайте один заголовок <h1> на кожну сторінку.",
                count=len(missing_h1),
            ))

        if multiple_h1:
            issues.append(self.create_issue(
                category="multiple_h1",
                severity=SeverityLevel.WARNING,
                message=f"Декілька H1: {len(multiple_h1)} сторінок",
                details="Рекомендується мати лише один H1 на сторінці для чіткої структури.",
                affected_urls=[url for url, _ in multiple_h1[:20]],
                recommendation="Залиште лише один H1, інші заголовки змініть на H2-H6.",
                count=len(multiple_h1),
            ))

        if empty_h1:
            issues.append(self.create_issue(
                category="empty_h1",
                severity=SeverityLevel.ERROR,
                message=f"Порожній H1: {len(empty_h1)} сторінок",
                details="H1 без тексту не несе жодної SEO-цінності.",
                affected_urls=empty_h1[:20],
                recommendation="Заповніть H1 релевантним текстом із ключовими словами.",
                count=len(empty_h1),
            ))

        if duplicate_h1s:
            dup_urls = []
            for h1, count in duplicate_h1s.items():
                urls_with_h1 = [url for url, h in all_h1s.items() if h == h1]
                dup_urls.extend(urls_with_h1[:5])

            issues.append(self.create_issue(
                category="duplicate_h1",
                severity=SeverityLevel.WARNING,
                message=f"Дублі H1: {len(duplicate_h1s)} груп дублікатів",
                details="Унікальний H1 допомагає розрізняти сторінки.",
                affected_urls=dup_urls[:20],
                recommendation="Створіть унікальний H1 для кожної сторінки.",
                count=sum(duplicate_h1s.values()),
            ))

        # Check heading hierarchy (H1-H6)
        hierarchy_violations = []
        for url, page in pages.items():
            if page.status_code != 200:
                continue
            headings_by_level = {
                1: page.h1_tags,
                2: page.h2_tags,
                3: page.h3_tags,
                4: page.h4_tags,
                5: page.h5_tags,
                6: page.h6_tags,
            }
            present_levels = sorted([lvl for lvl, tags in headings_by_level.items() if tags])
            if len(present_levels) >= 2:
                for i in range(len(present_levels) - 1):
                    if present_levels[i + 1] - present_levels[i] > 1:
                        hierarchy_violations.append(
                            (url, present_levels[i], present_levels[i + 1])
                        )
                        break

        if hierarchy_violations:
            issues.append(self.create_issue(
                category="hierarchy_violation",
                severity=SeverityLevel.WARNING,
                message=f"Порушення ієрархії заголовків: {len(hierarchy_violations)} сторінок",
                details="Пропуск рівнів заголовків (наприклад, H1 → H3 без H2) порушує семантику.",
                affected_urls=[url for url, _, _ in hierarchy_violations[:20]],
                recommendation="Дотримуйтесь послідовної ієрархії: H1 → H2 → H3 → H4.",
                count=len(hierarchy_violations),
            ))

        # Create table with problematic pages
        table_data = []

        for url in missing_h1[:10]:
            table_data.append({
                "URL": url,
                "Проблема": "Відсутній H1",
                "H1": "-",
            })

        for url, h1_list in multiple_h1[:10]:
            table_data.append({
                "URL": url,
                "Проблема": f"Декілька H1 ({len(h1_list)} шт.)",
                "H1": " | ".join(h1_list[:3]) + ("..." if len(h1_list) > 3 else ""),
            })

        for url in empty_h1[:10]:
            table_data.append({
                "URL": url,
                "Проблема": "Порожній H1",
                "H1": "(порожньо)",
            })

        for url, from_lvl, to_lvl in hierarchy_violations[:10]:
            table_data.append({
                "URL": url,
                "Проблема": f"H{from_lvl} → H{to_lvl} (пропуск)",
                "H1": page.h1_tags[0] if pages.get(url) and pages[url].h1_tags else "-",
            })

        if table_data:
            tables.append({
                "title": "Проблемні сторінки",
                "headers": ["URL", "Проблема", "H1"],
                "rows": table_data,
            })

        # Summary
        total_pages = len([p for p in pages.values() if p.status_code == 200])
        ok_pages = total_pages - len(missing_h1) - len(multiple_h1) - len(empty_h1)

        summary_parts = []
        if missing_h1:
            summary_parts.append(f"без H1: {len(missing_h1)}")
        if multiple_h1:
            summary_parts.append(f"декілька H1: {len(multiple_h1)}")
        if duplicate_h1s:
            summary_parts.append(f"дублів H1: {len(duplicate_h1s)}")
        if hierarchy_violations:
            summary_parts.append(f"порушень ієрархії: {len(hierarchy_violations)}")

        if summary_parts:
            summary = f"Знайдено проблеми: {', '.join(summary_parts)}"
        else:
            summary = f"Всі {total_pages} сторінок мають коректний H1"

        severity = self._determine_overall_severity(issues)

        return self.create_result(
            severity=severity,
            summary=summary,
            issues=issues,
            data={
                "total_pages": total_pages,
                "missing_h1": len(missing_h1),
                "multiple_h1": len(multiple_h1),
                "empty_h1": len(empty_h1),
                "duplicate_h1": len(duplicate_h1s),
                "hierarchy_violations": len(hierarchy_violations),
                "ok_pages": ok_pages,
            },
            tables=tables,
        )
