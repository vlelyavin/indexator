#!/usr/bin/env python3
"""Create comprehensive Ukrainian translation file from Russian."""

import json
import re

# Read Russian translations
with open('app/locales/ru.json', 'r', encoding='utf-8') as f:
    ru_data = json.load(f)

# Read existing Ukrainian translations (for reference)
with open('app/locales/uk.json', 'r', encoding='utf-8') as f:
    uk_existing = json.load(f)

# Russian to Ukrainian common translations
RU_UK_MAP = {
    # Common words
    "Да": "Так",
    "Нет": "Ні",
    "Ошибка": "Помилка",
    "Предупреждение": "Попередження",
    "Информация": "Інформація",
    "Успешно": "Успішно",
    "Найдено": "Знайдено",
    "Не найдено": "Не знайдено",
    "страниц": "сторінок",
    "проблем": "проблем",
    "Рекомендация": "Рекомендація",
    "Развернуть ещё": "Розгорнути ще",
    "Свернуть": "Згорнути",

    # Progress
    "Начинаем сканирование сайта...": "Розпочинаємо сканування сайту...",
    "Отсканировано": "Скановано",
    "Сканирование завершено. Найдено": "Сканування завершено. Знайдено",
    "Анализируем страницы...": "Аналізуємо сторінки...",
    "Анализ:": "Аналіз:",
    "Генерируем отчёт...": "Генеруємо звіт...",
    "Аудит завершён!": "Аудит завершено!",

    # SEO terms
    "Аудит": "Аудит",
    "Отчёт": "Звіт",
    "сгенерирован": "згенеровано",
    "Обзор": "Огляд",
    "Страниц отсканировано": "Сторінок скановано",
    "Проверок пройдено": "Перевірок пройдено",
    "Предупреждений": "Попереджень",
    "Критических проблем": "Критичних проблем",
    "Теоретическая справка": "Теоретична довідка",
    "Примеры": "Приклади",
    "Проблем не найдено": "Проблем не знайдено",
    "Скриншоты": "Скріншоти",
    "Экспресс-аудит сайта": "Експрес-аудит сайту",
}

def translate_ru_to_uk(text):
    """Translate Russian text to Ukrainian using simple replacements."""
    if not isinstance(text, str):
        return text

    result = text

    # Common replacements
    replacements = {
        # Alphabet
        'ы': 'и',
        'Ы': 'И',
        'э': 'е',
        'Э': 'Е',

        # Common words
        'все': 'всі',
        'Все': 'Всі',
        'для': 'для',
        'из': 'з',
        'на': 'на',
        'по': 'по',
        'не': 'не',
        'что': 'що',
        'это': 'це',
        'может': 'може',
        'если': 'якщо',
        'можно': 'можна',
        'нужно': 'потрібно',
        'должен': 'повинен',
        'должна': 'повинна',
        'должны': 'повинні',
        'есть': 'є',
        'был': 'був',
        'была': 'була',
        'были': 'були',
        'будет': 'буде',
        'будут': 'будуть',
        'более': 'більше',
        'менее': 'менше',
        'очень': 'дуже',
        'также': 'також',
        'только': 'тільки',
        'можно': 'можна',
        'нужно': 'потрібно',

        # SEO terms
        'сайта': 'сайту',
        'сайт': 'сайт',
        'страница': 'сторінка',
        'страницы': 'сторінки',
        'страниц': 'сторінок',
        'контент': 'контент',
        'контента': 'контенту',
        'ссылка': 'посилання',
        'ссылки': 'посилання',
        'ссылок': 'посилань',
        'изображение': 'зображення',
        'изображения': 'зображення',
        'изображений': 'зображень',
        'заголовок': 'заголовок',
        'заголовки': 'заголовки',
        'заголовков': 'заголовків',
        'поиск': 'пошук',
        'поиска': 'пошуку',
        'поисковый': 'пошуковий',
        'поисковая': 'пошукова',
        'поисковые': 'пошукові',
        'найдено': 'знайдено',
        'найден': 'знайдений',
        'найдена': 'знайдена',
        'найдены': 'знайдені',
        'отсутствует': 'відсутній',
        'отсутствуют': 'відсутні',
        'проблема': 'проблема',
        'проблемы': 'проблеми',
        'проблем': 'проблем',
        'ошибка': 'помилка',
        'ошибки': 'помилки',
        'ошибок': 'помилок',

        # Common verbs
        'проверьте': 'перевірте',
        'добавьте': 'додайте',
        'создайте': 'створіть',
        'используйте': 'використовуйте',
        'исправьте': 'виправте',
        'оптимизируйте': 'оптимізуйте',
        'улучшите': 'покращте',
        'настройте': 'налаштуйте',
        'установите': 'встановіть',
        'включите': 'увімкніть',
        'отключите': 'вимкніть',
        'убедитесь': 'переконайтеся',
        'рассмотрите': 'розгляньте',
        'ознакомьтесь': 'ознайомтеся',

        # Adjectives
        'уникальный': 'унікальний',
        'уникальная': 'унікальна',
        'уникальные': 'унікальні',
        'корректный': 'коректний',
        'корректная': 'коректна',
        'корректные': 'коректні',
        'правильный': 'правильний',
        'правильная': 'правильна',
        'правильные': 'правильні',
        'неправильный': 'неправильний',
        'неправильная': 'неправильна',
        'неправильные': 'неправильні',
        'хороший': 'хороший',
        'хорошая': 'хороша',
        'хорошие': 'хороші',
        'плохой': 'поганий',
        'плохая': 'погана',
        'плохие': 'погані',
        'важный': 'важливий',
        'важная': 'важлива',
        'важные': 'важливі',
        'основной': 'основний',
        'основная': 'основна',
        'основные': 'основні',
        'главный': 'головний',
        'главная': 'головна',
        'главные': 'головні',
        'пустой': 'порожній',
        'пустая': 'порожня',
        'пустые': 'порожні',
        'старый': 'старий',
        'старая': 'стара',
        'старые': 'старі',
        'новый': 'новий',
        'новая': 'нова',
        'новые': 'нові',
        'длинный': 'довгий',
        'длинная': 'довга',
        'длинные': 'довгі',
        'короткий': 'короткий',
        'короткая': 'коротка',
        'короткие': 'короткі',
        'высокий': 'високий',
        'высокая': 'висока',
        'высокие': 'високі',
        'низкий': 'низький',
        'низкая': 'низька',
        'низкие': 'низькі',
        'быстрый': 'швидкий',
        'быстрая': 'швидка',
        'быстрые': 'швидкі',
        'медленный': 'повільний',
        'медленная': 'повільна',
        'медленные': 'повільні',
    }

    # Apply replacements (case-sensitive)
    for ru_word, uk_word in replacements.items():
        result = result.replace(ru_word, uk_word)

    # Specific phrase replacements
    phrase_replacements = {
        'Судя по всему': 'Судячи з усього',
        'используется': 'використовується',
        'Платформу не удалось определить': 'Платформу не вдалося визначити',
        'на сайте': 'на сайті',
        'Также обнаружены признаки': 'Також виявлені ознаки',
        'Обнаруженные признаки': 'Виявлені ознаки',
        'может использовать': 'може використовувати',
        'несколько технологий': 'кілька технологій',
        'кастомную разработку': 'кастомну розробку',
        'неизвестную': 'невідому',
        'Ознакомьтесь с': 'Ознайомтеся з',
        'рекомендациями для': 'рекомендаціями для',
        'вашей платформы': 'вашої платформи',
    }

    for ru_phrase, uk_phrase in phrase_replacements.items():
        result = result.replace(ru_phrase, uk_phrase)

    return result

def translate_dict(data):
    """Recursively translate dictionary values."""
    if isinstance(data, dict):
        return {key: translate_dict(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [translate_dict(item) for item in data]
    elif isinstance(data, str):
        return translate_ru_to_uk(data)
    else:
        return data

# Create Ukrainian translation
uk_data = {}

# Copy and translate each section
for key, value in ru_data.items():
    if key in uk_existing:
        # Use existing Ukrainian translation if available
        uk_data[key] = uk_existing[key]
    else:
        # Translate from Russian
        uk_data[key] = translate_dict(value)

# Ensure analyzer_content section exists (translate from Russian)
if 'analyzer_content' in ru_data:
    uk_data['analyzer_content'] = translate_dict(ru_data['analyzer_content'])

# Merge with existing Ukrainian analyzer names/descriptions
if 'analyzers' in uk_existing:
    if 'analyzers' not in uk_data:
        uk_data['analyzers'] = {}
    for analyzer, trans in uk_existing['analyzers'].items():
        if analyzer not in uk_data['analyzers']:
            uk_data['analyzers'][analyzer] = {}
        if 'name' in trans:
            uk_data['analyzers'][analyzer]['name'] = trans['name']
        if 'description' in trans:
            uk_data['analyzers'][analyzer]['description'] = trans['description']

# Write new Ukrainian file
with open('app/locales/uk.json', 'w', encoding='utf-8') as f:
    json.dump(uk_data, f, ensure_ascii=False, indent=2)

print("Created comprehensive uk.json with analyzer_content section")
print(f"Total keys: {len(uk_data)}")
print(f"Has analyzer_content: {'analyzer_content' in uk_data}")
print(f"Has analyzers: {'analyzers' in uk_data}")
print(f"Has tables: {'tables' in uk_data}")
