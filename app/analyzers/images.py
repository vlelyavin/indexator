"""Images analyzer."""

import asyncio
from typing import Any, Dict, List
from urllib.parse import urlparse

from ..config import settings
from ..crawler import get_image_size
from ..models import AnalyzerResult, AuditIssue, ImageData, PageData, SeverityLevel
from .base import BaseAnalyzer


class ImagesAnalyzer(BaseAnalyzer):
    """Analyzer for image optimization (alt, format, size)."""

    name = "images"
    display_name = "Зображення"
    description = "Оптимізовані зображення покращують швидкість завантаження та доступність сайту."
    icon = ""
    theory = """<strong>Alt-атрибут</strong> — описує зміст зображення для пошукових систем, скрінрідерів та випадків коли зображення не завантажилось.

<strong>Правила Alt:</strong>
• Стисний опис до 125 символів з ключовими словами (без спаму)
• Не починайте з "Зображення..." або "Фото..."
• Для декоративних зображень — порожній <code>alt=""</code>

<strong>Формати зображень:</strong>
• <strong>WebP/AVIF</strong> — на 25-50% менше за JPEG, рекомендовані
• <strong>JPEG</strong> — фотографії, <strong>PNG</strong> — прозорість, <strong>SVG</strong> — векторна графіка
• Зображення понад 200 KB сповільнюють завантаження — стискайте та адаптуйте розмір"""

    LEGACY_FORMATS = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}
    MODERN_FORMATS = {'webp', 'avif', 'svg'}

    async def analyze(
        self,
        pages: Dict[str, PageData],
        base_url: str,
        **kwargs: Any
    ) -> AnalyzerResult:
        issues: List[AuditIssue] = []
        tables: List[Dict[str, Any]] = []

        # Collect all unique images
        all_images: Dict[str, Dict[str, Any]] = {}  # src -> {data, pages}

        for url, page in pages.items():
            if page.status_code != 200:
                continue

            for img in page.images:
                src = img.src
                if src not in all_images:
                    all_images[src] = {
                        'data': img,
                        'pages': [],
                    }
                all_images[src]['pages'].append(url)

        total_images = len(all_images)

        # Analyze images
        missing_alt = []
        empty_alt = []
        legacy_format = []
        large_images = []
        critical_images = []

        # Check image sizes (limit to first 50 for performance)
        images_to_check = list(all_images.keys())[:50]

        async def check_image_size(src: str) -> tuple[str, int | None]:
            size = await get_image_size(src)
            return src, size

        # Check sizes concurrently
        size_tasks = [check_image_size(src) for src in images_to_check]
        size_results = await asyncio.gather(*size_tasks, return_exceptions=True)

        image_sizes = {}
        for result in size_results:
            if isinstance(result, tuple):
                src, size = result
                if size is not None:
                    image_sizes[src] = size
                    all_images[src]['data'].size = size

        # Analyze each image
        for src, img_info in all_images.items():
            img: ImageData = img_info['data']
            pages_with_image = img_info['pages']

            # Check alt attribute
            if img.alt is None:
                missing_alt.append({
                    'src': src,
                    'pages': pages_with_image[:3],
                })
            elif img.alt.strip() == '':
                empty_alt.append({
                    'src': src,
                    'pages': pages_with_image[:3],
                })

            # Check format
            format_ext = img.format
            if not format_ext:
                # Try to extract from URL
                path = urlparse(src).path.lower()
                for ext in self.LEGACY_FORMATS | self.MODERN_FORMATS:
                    if path.endswith(f'.{ext}'):
                        format_ext = ext
                        break

            if format_ext and format_ext.lower() in self.LEGACY_FORMATS:
                legacy_format.append({
                    'src': src,
                    'format': format_ext,
                    'pages': pages_with_image[:3],
                })

            # Check size
            size = img.size or image_sizes.get(src)
            if size:
                if size > settings.IMAGE_CRITICAL_SIZE:
                    critical_images.append({
                        'src': src,
                        'size': size,
                        'pages': pages_with_image[:3],
                    })
                elif size > settings.IMAGE_WARNING_SIZE:
                    large_images.append({
                        'src': src,
                        'size': size,
                        'pages': pages_with_image[:3],
                    })

        # Create issues
        if missing_alt:
            issues.append(self.create_issue(
                category="missing_alt",
                severity=SeverityLevel.ERROR,
                message=f"Зображення без alt: {len(missing_alt)} шт.",
                details="Атрибут alt важливий для доступності та SEO. Пошукові системи використовують alt для розуміння вмісту зображень.",
                affected_urls=[img['src'] for img in missing_alt[:10]],
                recommendation="Додайте описовий alt атрибут до всіх зображень.",
                count=len(missing_alt),
            ))

        if empty_alt:
            issues.append(self.create_issue(
                category="empty_alt",
                severity=SeverityLevel.WARNING,
                message=f"Зображення з порожнім alt: {len(empty_alt)} шт.",
                details="Порожній alt допустимий лише для декоративних зображень.",
                affected_urls=[img['src'] for img in empty_alt[:10]],
                recommendation="Заповніть alt описом зображення або позначте як декоративне (role='presentation').",
                count=len(empty_alt),
            ))

        if legacy_format:
            issues.append(self.create_issue(
                category="legacy_format",
                severity=SeverityLevel.WARNING,
                message=f"Застарілий формат зображень: {len(legacy_format)} шт.",
                details="Формати JPEG та PNG можна замінити на WebP або AVIF для кращого стиснення.",
                affected_urls=[img['src'] for img in legacy_format[:10]],
                recommendation="Конвертуйте зображення у формат WebP. Це може зменшити розмір на 25-35%.",
                count=len(legacy_format),
            ))

        if critical_images:
            issues.append(self.create_issue(
                category="critical_size",
                severity=SeverityLevel.ERROR,
                message=f"Дуже великі зображення (>1 MB): {len(critical_images)} шт.",
                details="Зображення більше 1 MB критично сповільнюють завантаження сторінки.",
                affected_urls=[img['src'] for img in critical_images[:10]],
                recommendation="Зменшіть розмір зображень через стиснення та/або зміну роздільної здатності.",
                count=len(critical_images),
            ))

        if large_images:
            issues.append(self.create_issue(
                category="large_size",
                severity=SeverityLevel.WARNING,
                message=f"Великі зображення (>400 KB): {len(large_images)} шт.",
                details="Великі зображення сповільнюють завантаження, особливо на мобільних пристроях.",
                affected_urls=[img['src'] for img in large_images[:10]],
                recommendation="Оптимізуйте зображення або використовуйте lazy loading.",
                count=len(large_images),
            ))

        # Create table with problematic images
        def format_size(size: int) -> str:
            if size > 1024 * 1024:
                return f"{size / (1024 * 1024):.1f} MB"
            return f"{size / 1024:.0f} KB"

        table_data = []

        for img in critical_images[:10]:
            table_data.append({
                "URL зображення": img['src'][:80] + "..." if len(img['src']) > 80 else img['src'],
                "Розмір": format_size(img['size']),
                "Проблема": "Критичний розмір",
                "Сторінка": img['pages'][0] if img['pages'] else "-",
            })

        for img in large_images[:5]:
            table_data.append({
                "URL зображення": img['src'][:80] + "..." if len(img['src']) > 80 else img['src'],
                "Розмір": format_size(img['size']),
                "Проблема": "Великий розмір",
                "Сторінка": img['pages'][0] if img['pages'] else "-",
            })

        if table_data:
            tables.append({
                "title": "Проблемні зображення",
                "headers": ["URL зображення", "Розмір", "Проблема", "Сторінка"],
                "rows": table_data,
            })

        # Summary
        problems_count = len(missing_alt) + len(critical_images) + len(large_images)

        if not issues:
            summary = f"Всі {total_images} зображень оптимізовані"
        else:
            parts = []
            if missing_alt:
                parts.append(f"без alt: {len(missing_alt)}")
            if critical_images or large_images:
                parts.append(f"завеликі: {len(critical_images) + len(large_images)}")
            if legacy_format:
                parts.append(f"застарілий формат: {len(legacy_format)}")
            summary = f"Знайдено {total_images} зображень. Проблеми: {', '.join(parts)}"

        severity = self._determine_overall_severity(issues)

        return self.create_result(
            severity=severity,
            summary=summary,
            issues=issues,
            data={
                "total_images": total_images,
                "missing_alt": len(missing_alt),
                "empty_alt": len(empty_alt),
                "legacy_format": len(legacy_format),
                "large_images": len(large_images),
                "critical_images": len(critical_images),
                "largest_image": critical_images[0] if critical_images else (large_images[0] if large_images else None),
            },
            tables=tables,
        )
