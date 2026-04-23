# HackerOne Bug Hunter Research Sample

Решение тестового задания по исследованию и сбору данных об активных и ценных багхантерах HackerOne для задач привлечения исследователей на платформу Standoff.

## Что требовалось сделать

Задача была не в том, чтобы массово скачать всю платформу HackerOne, а в том, чтобы показать рабочий подход:

1. Понять, какие публичные данные о багхантерах полезны для оценки.
2. Выбрать источники и объяснить, почему они подходят.
3. Спроектировать структуру данных.
4. Реализовать небольшой, но воспроизводимый сбор.
5. Сохранить результат в удобном для анализа формате.
6. Сформулировать, как эти данные можно использовать для Standoff.

Основной фокус: найти исследователей, которые не просто имеют высокую общую репутацию, а подходят под конкретные scope и типы программ: Web, Mobile, Infrastructure, OWASP-категории, high/critical reports, публичная активность и наличие контактов.

## Как выполнялось задание

Сначала были изучены публичные страницы HackerOne: лидерборды, профили исследователей и Hacktivity. В лидербордах есть несколько полезных срезов: общая репутация, high/critical reputation, upvoted Hacktivity, up and comers, OWASP 2017 категории и asset type категории.

После этого был выбран подход через публичный GraphQL, который использует веб-интерфейс HackerOne. Это позволяет получать структурированные JSON-ответы и не зависеть от HTML-разметки страницы.

Пайплайн сбора:

1. Получить CSRF token с публичной страницы HackerOne.
2. Пройти по выбранным leaderboard views за Q1 и Q2 2026.
3. Взять до top 30 пользователей из каждой категории.
4. Собрать все leaderboard entries в общий список.
5. Дедуплицировать пользователей по `username`.
6. Для каждого уникального username запросить публичный профиль.
7. Для каждого username собрать публичную Hacktivity за последний год.
8. Собрать агрегированную карточку `researcher`.
9. Посчитать scope-метрики и `standoff_priority_score`.
10. Сохранить полный JSON и отдельные CSV-таблицы.

Если один профиль или Hacktivity-запрос падает, сбор не останавливается. Ошибка сохраняется в `metadata.profile_errors` или `metadata.hacktivity_errors`, а остальные данные продолжают собираться.

## Какие данные собираются

Основные группы данных:

|     Группа    |                   Примеры полей                               |                   Зачем нужны                |
|     ---       |                         ---                                   |                      ---                     |
| Идентификация | `username`, `name`, `profile_url`, `user_id`                  | Дедупликация и дальнейшая коммуникация       |
|  Лидерборды   | `leaderboard`, `rank`, `previous_rank`, `reputation`, `votes` | Первичный сигнал активности и специализации  |
|   Качество    | `signal`, `impact`, `valid_vulnerability_count`               | Оценка качества и полезности отчетов         |
| Специализация | OWASP, Asset Type, High/Critical                              | Матчинг исследователя под scope программы    |
|    Профиль    | `bio`, `intro`, `location`, `created_at`, `streak`            | Контекст опыта и устойчивости активности     |
|     Доверие   | `cleared`, `verified`                                         | Сигнал для приватных программ                |
|    Контакты   | GitHub, X/Twitter, LinkedIn, Bugcrowd, website                | Каналы привлечения и проверка внешнего следа |
|   Hacktivity  | публичные reports, programs, severity, bounty                 | Актуальная активность за последний год       |

## Как устроена структура данных

В JSON есть три основных уровня:

- `metadata` - параметры сбора, даты, лимиты, ссылки на leaderboard pages, ошибки.
- `leaderboards` - первичные строки лидербордов по категориям и кварталам.
- `researchers` - агрегированные карточки уникальных исследователей.

Для ручного анализа дополнительно создаются три CSV:

- `data/hackerone_hunters_sample.csv` - одна строка = один уникальный researcher.
- `data/hackerone_leaderboard_entries.csv` - одна строка = одно появление в leaderboard.
- `data/hackerone_hacktivity.csv` - одна строка = один публичный Hacktivity item.

Такое разделение нужно, чтобы не складывать все в одно поле CSV. Основная таблица подходит для сортировки и shortlist, а дополнительные таблицы позволяют провалиться в детали: где именно пользователь был найден и какие публичные Hacktivity items у него есть.

## Scope metrics и scoring

`standoff_priority_score` - это не метрика HackerOne. Это прикладная оценка для сортировки кандидатов под Standoff.

Score учитывает:

- репутацию;
- количество валидных уязвимостей;
- signal и impact за past year;
- количество появлений в лидербордах;
- количество кварталов и категорий, где пользователь найден;
- наличие OWASP и Asset Type специализаций;
- high/critical лидерборды;
- лучшие позиции в top 3/top 10/top 30;
- публичную Hacktivity за последний год;
- количество программ в Hacktivity;
- признаки `cleared`, `verified` и наличие публичных контактов.

Для очень больших счетчиков используется `log10`, чтобы один параметр вроде общей репутации не задавил остальные признаки. Для отдельных компонентов есть верхние ограничения через `min(..., cap)`, чтобы score оставался устойчивым и объяснимым.

Формула подробнее описана в `docs/REPORT.md`.

## Текущий собранный результат

Текущая выборка собрана за `2026`, кварталы `Q1,Q2`, `individual`, до `30` строк из каждой категории.

Собранные категории:

- Highest Reputation.
- Highest Critical Reputation.
- Most Upvoted Hacktivity.
- Up and Comers.
- OWASP 2017: Injection, Broken Authentication, Sensitive Data Exposure, XXE, Broken Access Control, Security Misconfiguration, XSS, Insecure Deserialization.
- Asset Types: Web Application, Android Mobile App, iOS Mobile App, Infrastructure, Source Code, AI Model.

Итоговый объем:

- 36 leaderboard views за Q1/Q2 2026.
- 1053 строки лидербордов до дедупликации.
- 610 уникальных researchers после дедупликации.
- 608 публичных профилей успешно обогащены.
- 5342 публичных Hacktivity item сохранены в CSV.
- Суммарный публичный `total_count` Hacktivity по найденным пользователям: 8197.

В двух leaderboard views HackerOne вернул меньше 30 строк: Q2 OWASP XXE - 20 и Q2 Asset Type Infrastructure - 13. Это сохранено как есть, без искусственного дополнения данных.

## Что внутри проекта

- `main.py` - CLI-точка входа: аргументы запуска и сохранение результатов.
- `hackerone_research/config.py` - параметры по умолчанию: год, квартал, лимит, пути к результатам.
- `hackerone_research/collector.py` - основной сценарий сбора: лидерборды, профили, Hacktivity, агрегация.
- `hackerone_research/hackerone/` - слой публичного HackerOne GraphQL: клиент, запросы, лидерборды, профили, Hacktivity.
- `hackerone_research/processing/` - дедупликация researchers, scope-метрики и `standoff_priority_score`.
- `hackerone_research/output/` - экспорт JSON/CSV и Excel-гиперссылки.
- `data/hackerone_hunters_sample.json` - полная структура: metadata, leaderboards, hacktivity, researchers.
- `data/hackerone_hunters_sample.csv` - плоская таблица исследователей для Excel/Google Sheets.
- `data/hackerone_leaderboard_entries.csv` - подробная таблица появлений в лидербордах.
- `data/hackerone_hacktivity.csv` - публичная Hacktivity найденных исследователей.
- `docs/REPORT.md` - подробный отчет по пунктам тестового задания.
- `HackerOne.txt` - исходные заметки по страницам и фильтрам HackerOne.

## Быстрый запуск

```powershell
.\.venv\Scripts\python.exe .\main.py
```

Полный запуск с явными параметрами:

```powershell
.\.venv\Scripts\python.exe .\main.py --year 2026 --quarters 1,2 --limit 30 --delay 0.7 --hacktivity-limit 50
```

Быстрый тестовый запуск на малом объеме:

```powershell
.\.venv\Scripts\python.exe .\main.py --limit 5 --max-profiles 10 --hacktivity-limit 10
```

Запуск без Hacktivity, если нужно быстро проверить лидерборды и профили:

```powershell
.\.venv\Scripts\python.exe .\main.py --limit 5 --skip-hacktivity
```

Период Hacktivity можно задать явно:

```powershell
.\.venv\Scripts\python.exe .\main.py --hacktivity-start-date 2025-04-20 --hacktivity-end-date 2026-04-20
```

## CSV и Excel

CSV пишется с разделителем `;` и кодировкой `UTF-8 with BOM`, чтобы Excel в русской локали открывал файл по колонкам без ручного импорта.

Поля `profile_url`, `website`, `github`, `twitter`, `linkedin`, `bugcrowd`, `gitlab`, `report_url` и `team_url` экспортируются как Excel-формулы `ГИПЕРССЫЛКА`. Это сделано, чтобы ссылки были кликабельными в Excel.

Дробные числа в CSV экспортируются с запятой, например `14,78`, а не `14.78`. Это нужно для русской локали Excel: иначе значения вроде `5.53` могут автоматически превращаться в даты.

## Проверка

Проверка синтаксиса:

```powershell
.\.venv\Scripts\python.exe -m py_compile main.py hackerone_research\collector.py hackerone_research\config.py hackerone_research\hackerone\client.py hackerone_research\hackerone\leaderboards.py hackerone_research\hackerone\profiles.py hackerone_research\hackerone\hacktivity.py hackerone_research\hackerone\queries.py hackerone_research\processing\researchers.py hackerone_research\processing\scoring.py hackerone_research\output\exporters.py
```

Проверка CLI:

```powershell
.\.venv\Scripts\python.exe .\main.py --help
```

## Ограничения

- Используются только публичные данные, без логина и без приватных отчетов.
- Публичный GraphQL веб-интерфейса не является официальным стабильным API, схема может измениться.
- Официальный HackerOne API требует API-токен для многих программных и отчетных ресурсов.
- Публичные профили могут быть неполными: не все исследователи указывают соцсети, локацию или открытость к работе.
- Score является аналитическим ранжированием для shortlist, а не официальной оценкой HackerOne.

## Источники

- [HackerOne Leaderboards](https://docs.hackerone.com/en/articles/8456255-leaderboards/)
- [90-Day Leaderboard](https://docs.hackerone.com/en/articles/8456917-90-day-leaderboard)
- [HackerOne API Getting Started](https://api.hackerone.com/getting-started/)
