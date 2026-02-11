"""HTTPS and security headers analyzer."""

import re
from typing import Any, Dict, List

from ..models import AnalyzerResult, AuditIssue, PageData, SeverityLevel
from .base import BaseAnalyzer


class SecurityAnalyzer(BaseAnalyzer):
    """Analyzer for HTTPS usage, security headers, and mixed content."""

    name = "security"
    icon = ""

    def __init__(self):
        super().__init__()

    @property
    def display_name(self) -> str:
        return self.t("analyzers.security.name")

    @property
    def description(self) -> str:
        return self.t("analyzers.security.description")

    @property
    def theory(self) -> str:
        return self.t("analyzers.security.theory")

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
                message=self.t("analyzers.security.no_https"),
                details=self.t("analyzers.security.no_https_details"),
                recommendation=self.t("analyzers.security.no_https_recommendation"),
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
                "message": self.t("analyzers.security.missing_hsts"),
                "details": self.t("analyzers.security.missing_hsts_details"),
                "recommendation": self.t("analyzers.security.missing_hsts_recommendation"),
            },
            "x-content-type-options": {
                "name": "X-Content-Type-Options",
                "category": "missing_x_content_type",
                "severity": SeverityLevel.INFO,
                "message": self.t("analyzers.security.missing_x_content_type"),
                "details": self.t("analyzers.security.missing_x_content_type_details"),
                "recommendation": self.t("analyzers.security.missing_x_content_type_recommendation"),
                "expected_value": "nosniff",
            },
            "x-frame-options": {
                "name": "X-Frame-Options",
                "category": "missing_x_frame",
                "severity": SeverityLevel.INFO,
                "message": self.t("analyzers.security.missing_x_frame"),
                "details": self.t("analyzers.security.missing_x_frame_details"),
                "recommendation": self.t("analyzers.security.missing_x_frame_recommendation"),
                "expected_values": ["deny", "sameorigin"],
            },
            "content-security-policy": {
                "name": "Content-Security-Policy (CSP)",
                "category": "missing_csp",
                "severity": SeverityLevel.INFO,
                "message": self.t("analyzers.security.missing_csp"),
                "details": self.t("analyzers.security.missing_csp_details"),
                "recommendation": self.t("analyzers.security.missing_csp_recommendation"),
            },
        }

        if home_page and home_page.response_headers:
            response_headers_lower = {k.lower(): v for k, v in home_page.response_headers.items()}

            for header_key, header_info in security_headers.items():
                header_value = response_headers_lower.get(header_key)

                if header_value:
                    # Header present — check value if needed
                    status = self.t("analyzers.security.status_present")
                    value_display = header_value[:80]

                    if "expected_value" in header_info:
                        if header_value.lower().strip() != header_info["expected_value"]:
                            status = self.t("analyzers.security.status_invalid")

                    if "expected_values" in header_info:
                        if header_value.lower().strip() not in header_info["expected_values"]:
                            status = self.t("analyzers.security.status_invalid")

                    headers_status[header_key] = {
                        "name": header_info["name"],
                        "status": status,
                        "value": value_display,
                    }
                else:
                    # Header missing
                    headers_status[header_key] = {
                        "name": header_info["name"],
                        "status": self.t("analyzers.security.status_missing"),
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
                    "status": self.t("analyzers.security.status_unknown"),
                    "value": self.t("analyzers.security.status_check_failed"),
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
                message=self.t("analyzers.security.mixed_content", count=len(pages_with_mixed_content)),
                details=self.t("analyzers.security.mixed_content_details"),
                affected_urls=pages_with_mixed_content[:20],
                recommendation=self.t("analyzers.security.mixed_content_recommendation"),
                count=len(pages_with_mixed_content),
            ))

        # 4. If no issues at all — everything is fine
        if not issues:
            issues.append(self.create_issue(
                category="security_ok",
                severity=SeverityLevel.SUCCESS,
                message=self.t("analyzers.security.security_ok"),
                details=self.t("analyzers.security.security_ok_details"),
            ))

        # 5. Build security headers table
        h_header = self.t("table.header")
        h_status = self.t("table.status")
        h_value = self.t("table.value")

        table_rows = []
        for header_key in security_headers:
            info = headers_status.get(header_key, {})
            table_rows.append({
                h_header: info.get("name", header_key),
                h_status: info.get("status", self.t("analyzers.security.status_unknown")),
                h_value: info.get("value", "-"),
            })

        tables.append({
            "title": self.t("analyzers.security.table_title"),
            "headers": [h_header, h_status, h_value],
            "rows": table_rows[:10],
        })

        # 6. Summary
        severity = self._determine_overall_severity(issues)

        if severity == SeverityLevel.SUCCESS:
            summary = self.t("analyzers.security.summary_ok")
        else:
            error_count = sum(1 for i in issues if i.severity == SeverityLevel.ERROR)
            warning_count = sum(1 for i in issues if i.severity == SeverityLevel.WARNING)
            info_count = sum(1 for i in issues if i.severity == SeverityLevel.INFO)
            parts = []
            if error_count:
                parts.append(self.t("analyzers.security.summary_errors", count=error_count))
            if warning_count:
                parts.append(self.t("analyzers.security.summary_warnings", count=warning_count))
            if info_count:
                parts.append(self.t("analyzers.security.summary_info", count=info_count))
            summary = self.t("analyzers.security.summary_issues", issues=", ".join(parts))

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
