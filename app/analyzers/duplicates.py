"""Duplicate content analyzer."""

import re
from typing import Any, Dict, List, Tuple

from bs4 import BeautifulSoup

from ..models import AnalyzerResult, AuditIssue, PageData, SeverityLevel
from .base import BaseAnalyzer


class DuplicatesAnalyzer(BaseAnalyzer):
    """Analyzer for duplicate content detection."""

    name = "duplicates"
    display_name = "Дублікати контенту"
    description = "Виявлення сторінок зі схожим або ідентичним контентом."
    icon = ""
    theory = """<strong>Дублікати контенту</strong> — сторінки з ідентичним або дуже схожим текстом. Google не штрафує за дублікати, але обирає лише одну версію для індексації, інші ігноруються.

<strong>Типи дублікатів:</strong>
• <strong>Точні дублікати</strong> — повністю ідентичний контент на різних URL
• <strong>Близькі дублікати</strong> — сторінки зі схожим текстом (>80% збіг)
• <strong>Внутрішні дублікати</strong> — через параметри URL, www/non-www, http/https

<strong>Як виправити:</strong>
• Встановіть канонічний тег (rel="canonical") на основну версію
• Налаштуйте 301 редирект з дублікатів на оригінал
• Додайте noindex для службових або фільтрованих сторінок"""

    def _extract_text(self, html_content: str) -> str:
        """Extract and normalize text from HTML."""
        soup = BeautifulSoup(html_content, "lxml")
        # Remove script and style elements
        for element in soup(["script", "style", "noscript"]):
            element.decompose()
        text = soup.get_text(separator=" ")
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip().lower()
        return text

    def _create_shingles(self, text: str, shingle_size: int = 3) -> set:
        """Create shingles (n-word sets) from text."""
        words = text.split()
        if len(words) < shingle_size:
            return set()
        shingles = set()
        for i in range(len(words) - shingle_size + 1):
            shingle = tuple(words[i:i + shingle_size])
            shingles.add(shingle)
        return shingles

    def _create_minhash_signature(self, shingles: set, num_hashes: int = 100) -> List[int]:
        """Create a MinHash signature from shingles."""
        if not shingles:
            return [0] * num_hashes
        signature = []
        for seed in range(num_hashes):
            min_hash = float("inf")
            for shingle in shingles:
                h = hash(shingle) ^ seed
                if h < min_hash:
                    min_hash = h
            signature.append(min_hash)
        return signature

    def _estimate_jaccard(self, sig1: List[int], sig2: List[int]) -> float:
        """Estimate Jaccard similarity from two MinHash signatures."""
        if not sig1 or not sig2:
            return 0.0
        matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
        return matches / len(sig1)

    async def analyze(
        self,
        pages: Dict[str, PageData],
        base_url: str,
        **kwargs: Any
    ) -> AnalyzerResult:
        issues: List[AuditIssue] = []
        tables: List[Dict[str, Any]] = []

        # Step 1: Build MinHash signatures for eligible pages
        signatures: Dict[str, List[int]] = {}
        word_counts: Dict[str, int] = {}

        for url, page in pages.items():
            if page.status_code != 200 or page.word_count <= 50 or not page.html_content:
                continue

            text = self._extract_text(page.html_content)
            shingles = self._create_shingles(text, shingle_size=3)
            if not shingles:
                continue

            signature = self._create_minhash_signature(shingles, num_hashes=100)
            signatures[url] = signature
            word_counts[url] = page.word_count

        # Step 2: Compare all pages pairwise
        urls = list(signatures.keys())
        exact_duplicate_pairs: List[Tuple[str, str, float]] = []
        near_duplicate_pairs: List[Tuple[str, str, float]] = []

        for i in range(len(urls)):
            for j in range(i + 1, len(urls)):
                url_a = urls[i]
                url_b = urls[j]

                # Only compare if word counts are within 50% range of each other
                wc_a = word_counts[url_a]
                wc_b = word_counts[url_b]
                if wc_a == 0 or wc_b == 0:
                    continue
                ratio = min(wc_a, wc_b) / max(wc_a, wc_b)
                if ratio < 0.5:
                    continue

                jaccard = self._estimate_jaccard(signatures[url_a], signatures[url_b])

                if jaccard >= 0.95:
                    exact_duplicate_pairs.append((url_a, url_b, jaccard))
                elif jaccard >= 0.80:
                    near_duplicate_pairs.append((url_a, url_b, jaccard))

        # Step 3: Group duplicates using simple union-find
        def group_pairs(pairs: List[Tuple[str, str, float]]) -> List[set]:
            """Group URLs that are connected through duplicate pairs."""
            parent: Dict[str, str] = {}

            def find(x: str) -> str:
                while parent.get(x, x) != x:
                    parent[x] = parent.get(parent[x], parent[x])
                    x = parent[x]
                return x

            def union(x: str, y: str) -> None:
                rx, ry = find(x), find(y)
                if rx != ry:
                    parent[rx] = ry

            for url_a, url_b, _ in pairs:
                parent.setdefault(url_a, url_a)
                parent.setdefault(url_b, url_b)
                union(url_a, url_b)

            groups: Dict[str, set] = {}
            for url in parent:
                root = find(url)
                if root not in groups:
                    groups[root] = set()
                groups[root].add(url)

            return [group for group in groups.values() if len(group) > 1]

        exact_groups = group_pairs(exact_duplicate_pairs)
        near_groups = group_pairs(near_duplicate_pairs)

        # Step 4: Create issues
        if not exact_duplicate_pairs and not near_duplicate_pairs:
            issues.append(self.create_issue(
                category="no_duplicates",
                severity=SeverityLevel.SUCCESS,
                message="Дублікатів не виявлено",
                details=f"Перевірено {len(signatures)} сторінок — дублікатів контенту не знайдено.",
                recommendation="Продовжуйте створювати унікальний контент для кожної сторінки.",
            ))

        if exact_groups:
            affected = []
            for group in exact_groups:
                affected.extend(list(group))
            issues.append(self.create_issue(
                category="exact_duplicates",
                severity=SeverityLevel.ERROR,
                message=f"Точні дублікати: {len(exact_groups)} груп",
                details="Сторінки з практично ідентичним контентом. Google обере лише одну версію для індексації.",
                affected_urls=list(set(affected))[:20],
                recommendation="Встановіть канонічний тег (rel=\"canonical\") або налаштуйте 301 редирект на основну версію сторінки.",
                count=len(exact_groups),
            ))

        if near_groups:
            affected = []
            for group in near_groups:
                affected.extend(list(group))
            issues.append(self.create_issue(
                category="near_duplicates",
                severity=SeverityLevel.WARNING,
                message=f"Близькі дублікати: {len(near_groups)} груп",
                details="Сторінки зі схожим контентом (більше 80% збігу). Можуть конкурувати між собою в пошуковій видачі.",
                affected_urls=list(set(affected))[:20],
                recommendation="Об'єднайте схожі сторінки або додайте унікальний контент для кожної з них.",
                count=len(near_groups),
            ))

        # Step 5: Create table
        table_data = []
        all_pairs = (
            [(a, b, sim, "Точний") for a, b, sim in exact_duplicate_pairs]
            + [(a, b, sim, "Близький") for a, b, sim in near_duplicate_pairs]
        )
        all_pairs.sort(key=lambda x: x[2], reverse=True)

        for url_a, url_b, similarity, dup_type in all_pairs[:10]:
            table_data.append({
                "URL 1": url_a[:70] + "..." if len(url_a) > 70 else url_a,
                "URL 2": url_b[:70] + "..." if len(url_b) > 70 else url_b,
                "Подібність": f"{similarity:.0%}",
            })

        if table_data:
            tables.append({
                "title": "Дублікати контенту",
                "headers": ["URL 1", "URL 2", "Подібність"],
                "rows": table_data,
            })

        # Step 6: Summary
        total_groups = len(exact_groups) + len(near_groups)
        if total_groups > 0:
            summary = f"Знайдено {total_groups} груп дублікатів"
        else:
            summary = "Дублікатів не виявлено"

        severity = self._determine_overall_severity(issues)

        return self.create_result(
            severity=severity,
            summary=summary,
            issues=issues,
            data={
                "pages_analyzed": len(signatures),
                "exact_duplicate_groups": len(exact_groups),
                "near_duplicate_groups": len(near_groups),
                "exact_duplicate_pairs": len(exact_duplicate_pairs),
                "near_duplicate_pairs": len(near_duplicate_pairs),
            },
            tables=tables,
        )
