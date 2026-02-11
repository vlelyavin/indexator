"""HTTPS and security headers analyzer."""

import re
from typing import Any, Dict, List

from ..models import AnalyzerResult, AuditIssue, PageData, SeverityLevel
from .base import BaseAnalyzer


class SecurityAnalyzer(BaseAnalyzer):
    """Analyzer for HTTPS usage, security headers, and mixed content."""

    name = "security"
    display_name = "HTTPS та безпека"
    description = "Перевірка HTTPS, заголовків безпеки та змішаного контенту."
    icon = ""
    theory = """<strong>HTTPS як фактор ранжування.</strong> З 2014 року Google враховує HTTPS як сигнал ранжування. Сайти без SSL-сертифіката втрачають позиції та довіру користувачів.

<strong>Заголовки безпеки:</strong>
• <strong>HSTS</strong> (Strict-Transport-Security) — примушує браузер завжди використовувати HTTPS
• <strong>X-Content-Type-Options: nosniff</strong> — забороняє браузеру визначати MIME-тип самостійно
• <strong>X-Frame-Options</strong> (DENY/SAMEORIGIN) — захист від clickjacking-атак
• <strong>Content-Security-Policy</strong> — контролює джерела завантаження ресурсів

<strong>Змішаний контент</strong> — завантаження HTTP-ресурсів на HTTPS-сторінці. Браузери блокують такі ресурси, що призводить до помилок відображення та втрати довіри."""

    async def analyze(
        self,
        pages: Dict[str, PageData],
        base_url: str,
        **kwargs: Any
    ) -> AnalyzerResult:
        issues: List[AuditIssue] = []
        tables: List[Dict[str, Any]] = []

        is_https = base_url.startswith("https://")

        # 1. Check if site uses HTTPS
        if not is_https:
            issues.append(self.create_issue(
                category="no_https",
                severity=SeverityLevel.ERROR,
                message="Сайт не використовує HTTPS",
                details="HTTPS є фактором ранжування Google з 2014 року. Без SSL-сертифіката сайт позначається як небезпечний.",
                recommendation="Встановіть SSL-сертифікат та налаштуйте перенаправлення з HTTP на HTTPS.",
            ))

        # 2. Check security headers on homepage
        home_page = pages.get(base_url) or pages.get(base_url.rstrip("/") + "/")
        if not home_page:
            for url, page in pages.items():
                if page.status_code == 200:
                    home_page = page
                    break

        headers_status: Dict[str, Dict[str, str]] = {}
        security_headers = {
            "strict-transport-security": {
                "name": "Strict-Transport-Security (HSTS)",
                "category": "missing_hsts",
                "severity": SeverityLevel.WARNING,
                "message": "Відсутній заголовок HSTS",
                "details": "HSTS примушує браузер завжди використовувати HTTPS-з'єднання.",
                "recommendation": "Додайте заголовок: Strict-Transport-Security: max-age=31536000; includeSubDomains",
            },
            "x-content-type-options": {
                "name": "X-Content-Type-Options",
                "category": "missing_x_content_type",
                "severity": SeverityLevel.INFO,
                "message": "Відсутній X-Content-Type-Options",
                "details": "Заголовок X-Content-Type-Options: nosniff запобігає MIME-sniffing атакам.",
                "recommendation": "Додайте заголовок: X-Content-Type-Options: nosniff",
                "expected_value": "nosniff",
            },
            "x-frame-options": {
                "name": "X-Frame-Options",
                "category": "missing_x_frame",
                "severity": SeverityLevel.INFO,
                "message": "Відсутній X-Frame-Options",
                "details": "Заголовок X-Frame-Options захищає від clickjacking-атак.",
                "recommendation": "Додайте заголовок: X-Frame-Options: DENY або SAMEORIGIN",
                "expected_values": ["deny", "sameorigin"],
            },
            "content-security-policy": {
                "name": "Content-Security-Policy (CSP)",
                "category": "missing_csp",
                "severity": SeverityLevel.INFO,
                "message": "Відсутній Content-Security-Policy",
                "details": "CSP контролює, з яких джерел дозволено завантажувати ресурси на сторінці.",
                "recommendation": "Налаштуйте Content-Security-Policy для контролю джерел ресурсів.",
            },
        }

        if home_page and home_page.response_headers:
            response_headers_lower = {k.lower(): v for k, v in home_page.response_headers.items()}

            for header_key, header_info in security_headers.items():
                header_value = response_headers_lower.get(header_key)

                if header_value:
                    # Header present — check value if needed
                    status = "✓ Присутній"
                    value_display = header_value[:80]

                    if "expected_value" in header_info:
                        if header_value.lower().strip() != header_info["expected_value"]:
                            status = "⚠ Некоректне значення"

                    if "expected_values" in header_info:
                        if header_value.lower().strip() not in header_info["expected_values"]:
                            status = "⚠ Некоректне значення"

                    headers_status[header_key] = {
                        "name": header_info["name"],
                        "status": status,
                        "value": value_display,
                    }
                else:
                    # Header missing
                    headers_status[header_key] = {
                        "name": header_info["name"],
                        "status": "✗ Відсутній",
                        "value": "-",
                    }
                    issues.append(self.create_issue(
                        category=header_info["category"],
                        severity=header_info["severity"],
                        message=header_info["message"],
                        details=header_info["details"],
                        recommendation=header_info["recommendation"],
                    ))
        else:
            # No homepage found or no headers — mark all as unknown
            for header_key, header_info in security_headers.items():
                headers_status[header_key] = {
                    "name": header_info["name"],
                    "status": "? Невідомо",
                    "value": "Не вдалося перевірити",
                }

        # 3. Check for mixed content on HTTPS pages
        mixed_content_pattern = re.compile(
            r'(?:src|href)\s*=\s*["\']http://[^"\']+["\']',
            re.IGNORECASE
        )
        resource_tag_pattern = re.compile(
            r'<(?:img|script|iframe|source|video|audio|embed|object)\s[^>]*src\s*=\s*["\']http://[^"\']+["\']',
            re.IGNORECASE
        )
        stylesheet_pattern = re.compile(
            r'<link\s[^>]*rel\s*=\s*["\']stylesheet["\'][^>]*href\s*=\s*["\']http://[^"\']+["\']',
            re.IGNORECASE
        )
        stylesheet_pattern_alt = re.compile(
            r'<link\s[^>]*href\s*=\s*["\']http://[^"\']+["\'][^>]*rel\s*=\s*["\']stylesheet["\']',
            re.IGNORECASE
        )

        pages_with_mixed_content: List[str] = []

        for url, page in pages.items():
            if page.status_code != 200 or not page.html_content:
                continue

            if not url.startswith("https://"):
                continue

            html = page.html_content
            has_mixed = False

            # Check resource tags (img, script, iframe, etc.)
            if resource_tag_pattern.search(html):
                has_mixed = True

            # Check stylesheet links
            if not has_mixed and (stylesheet_pattern.search(html) or stylesheet_pattern_alt.search(html)):
                has_mixed = True

            if has_mixed:
                pages_with_mixed_content.append(url)

        if pages_with_mixed_content:
            issues.append(self.create_issue(
                category="mixed_content",
                severity=SeverityLevel.ERROR,
                message=f"Змішаний контент: {len(pages_with_mixed_content)} сторінок",
                details="Знайдено HTTP-ресурси (зображення, скрипти, стилі) на HTTPS-сторінках. Браузери можуть блокувати такі ресурси.",
                affected_urls=pages_with_mixed_content[:20],
                recommendation="Замініть усі HTTP-посилання на ресурси на HTTPS або використовуйте протокол-відносні URL.",
                count=len(pages_with_mixed_content),
            ))

        # 4. If no issues at all — everything is fine
        if not issues:
            issues.append(self.create_issue(
                category="security_ok",
                severity=SeverityLevel.SUCCESS,
                message="HTTPS та безпека в нормі",
                details="Сайт використовує HTTPS, основні заголовки безпеки присутні, змішаний контент не виявлено.",
            ))

        # 5. Build security headers table
        table_rows = []
        for header_key in security_headers:
            info = headers_status.get(header_key, {})
            table_rows.append({
                "Заголовок": info.get("name", header_key),
                "Статус": info.get("status", "? Невідомо"),
                "Значення": info.get("value", "-"),
            })

        tables.append({
            "title": "Заголовки безпеки",
            "headers": ["Заголовок", "Статус", "Значення"],
            "rows": table_rows[:10],
        })

        # 6. Summary
        severity = self._determine_overall_severity(issues)

        if severity == SeverityLevel.SUCCESS:
            summary = "HTTPS та безпека в нормі"
        else:
            error_count = sum(1 for i in issues if i.severity == SeverityLevel.ERROR)
            warning_count = sum(1 for i in issues if i.severity == SeverityLevel.WARNING)
            info_count = sum(1 for i in issues if i.severity == SeverityLevel.INFO)
            parts = []
            if error_count:
                parts.append(f"помилок: {error_count}")
            if warning_count:
                parts.append(f"попереджень: {warning_count}")
            if info_count:
                parts.append(f"інфо: {info_count}")
            summary = f"Знайдено проблем: {', '.join(parts)}"

        return self.create_result(
            severity=severity,
            summary=summary,
            issues=issues,
            data={
                "is_https": is_https,
                "mixed_content_pages": len(pages_with_mixed_content),
                "headers_checked": len(security_headers),
                "headers_present": sum(
                    1 for h in headers_status.values()
                    if h.get("status", "").startswith("✓")
                ),
            },
            tables=tables,
        )
