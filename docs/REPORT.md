# Отчет по тестовому заданию

Тема: исследование и сбор данных о багхантерах HackerOne для проектирования процессов привлечения и работы с исследователями на платформе Standoff.

## 1. Анализ задачи и ход мышления

Я понимаю задачу не как массовый парсинг всей платформы HackerOne, а как проверку подхода: какие данные о багхантерах стоит собирать, как их структурировать, как получить ограниченную, но полезную выборку и как превратить ее в решения для привлечения исследователей.

Основные подзадачи:

1. Найти публичные источники, где HackerOne уже ранжирует или описывает исследователей.
2. Определить признаки ценности и активности: лидерборды, репутация, signal/impact, валидные уязвимости, специализация, публичные контакты.
3. Спроектировать структуру данных, которая отделяет первичные факты от производных оценок.
4. Реализовать воспроизводимый сбор на небольшом объеме.
5. Сохранить данные в формате, удобном и для кода, и для ручного анализа.
6. Сформулировать выводы и способы применения этих данных в Standoff.

Порядок работы:

1. Проверил публичные страницы лидербордов и профилей HackerOne.
2. Изучил, какие данные фронтенд HackerOne получает через GraphQL.
3. Выбрал несколько разных лидербордов, чтобы получить не только общий топ, но и специализации.
4. Для найденных пользователей обогатил данные публичными профилями.
5. Нормализовал данные в JSON и CSV.
6. Добавил производный `standoff_priority_score`, чтобы показать, как из сырых признаков можно делать shortlist.

Риски и ограничения:

- Публичный GraphQL веб-интерфейса не является официальным стабильным API. Схема может измениться.
- Официальный HackerOne API требует токен; без него недоступны многие данные по отчетам, программам, выплатам и приватным приглашениям.
- Публичные профили могут быть неполными: не все указывают локацию, соцсети или открытость к работе.
- Лидерборды отражают выбранный период, фильтр и методику HackerOne. Их нельзя считать полной оценкой исследователя.
- Сбор должен быть ограниченным и аккуратным: задержки между запросами, маленький лимит, отсутствие обхода приватных данных.

## 2. Определение данных

Важные данные о багхантерах в этом контексте:

| Группа | Поля | Зачем нужны |
| --- | --- | --- |
| Идентификация | username, name, profile_url, user_id | Дедупликация и дальнейшая коммуникация |
| Позиции в лидербордах | leaderboard, rank, previous_rank, reputation/votes | Первичный сигнал активности и ценности |
| Качество | signal, impact, valid_vulnerability_count | Оценка полезности отчетов и среднего влияния |
| Специализация | OWASP Injection, Web App, High/Critical | Матчинг под типы программ Standoff |
| Профиль | bio, intro, location, created_at, streak | Контекст опыта и устойчивости активности |
| Доверие | cleared, verified | Сигнал для приватных программ и чувствительных scope |
| Контакты и внешний след | website, GitHub, LinkedIn, Twitter, Bugcrowd, HTB | Каналы привлечения и проверка экспертизы |

Как я определяю "ценного и активного" участника:

- Ценный: высокий impact, высокая репутация, много валидных уязвимостей, присутствие в high/critical или профильных лидербордах.
- Активный: присутствие в квартальных лидербордах, streak, свежая статистика signal/impact за past year, появление в нескольких категориях.
- Практически полезный для Standoff: есть специализация, публичные контакты, верификация/cleared, понятный профиль и релевантность Web/API/Mobile/Infra scope.

Первичные данные:

- Позиции в лидербордах HackerOne.
- Публичные поля профиля.
- Публичные счетчики valid vulnerabilities, reputation, signal, impact, streak.

Производные данные:

- `leaderboard_appearances` - сколько раз пользователь встречен в выбранных лидербордах.
- `best_observed_rank` - лучшая позиция в выбранной выборке.
- `leaderboard_categories` - набор категорий, где пользователь заметен.
- `standoff_priority_score` - прикладная оценка для shortlist, рассчитанная из публичных метрик.

## 3. Структура данных

Я разделяю данные на три уровня:

1. `metadata` - параметры сбора, время, ссылки на источники, ограничения и ошибки профилей.
2. `leaderboards` - первичные строки лидербордов по категориям.
3. `researchers` - агрегированная карточка исследователя с профилем, метриками и производными признаками.

Основные сущности:

| Сущность | Назначение |
| --- | --- |
| Researcher | Человек или аккаунт HackerOne |
| LeaderboardEntry | Факт позиции в конкретном лидерборде |
| Profile | Публичная карточка пользователя |
| SocialHandle | Внешний канал или профиль |
| DerivedScore | Производная оценка приоритета для Standoff |

Связи:

- `Researcher 1:N LeaderboardEntry` - один исследователь может входить в несколько лидербордов.
- `Researcher 1:1 Profile` - публичный профиль HackerOne.
- `Researcher 1:N SocialHandle` - внешние профили.
- `Researcher 1:1 DerivedScore` - расчетная оценка для конкретной методики.

Выходные форматы:

- JSON удобен для повторной обработки, сохранения вложенных данных и передачи в пайплайн.
- CSV удобен для быстрой сортировки в Excel/Google Sheets и ручного анализа рекрутером или program manager.

## 4. Сбор данных

Реализация разнесена по модулям:

- `main.py` - CLI-точка входа.
- `hackerone_research/config.py` - настройки по умолчанию.
- `hackerone_research/collector.py` - orchestration полного сбора.
- `hackerone_research/hackerone/client.py` - HTTP/GraphQL клиент.
- `hackerone_research/hackerone/queries.py` - GraphQL-запросы.
- `hackerone_research/hackerone/leaderboards.py` - категории лидербордов и сбор leaderboard entries.
- `hackerone_research/hackerone/profiles.py` - публичные профили и соцсети.
- `hackerone_research/hackerone/hacktivity.py` - публичная Hacktivity за выбранный период.
- `hackerone_research/processing/researchers.py` - дедупликация и агрегированная карточка исследователя.
- `hackerone_research/processing/scoring.py` - scope-метрики и `standoff_priority_score`.
- `hackerone_research/output/exporters.py` - JSON/CSV экспорт.

Команда, которой была собрана текущая выборка:

```powershell
.\.venv\Scripts\python.exe .\main.py --year 2026 --quarters 1,2 --limit 30 --delay 0.3 --hacktivity-limit 50 --hacktivity-page-size 25
```

Собранные публичные лидерборды:

- Highest Reputation.
- Highest Critical Reputation.
- Most Upvoted Hacktivity.
- Up and Comers.
- OWASP 2017: Injection, Broken Authentication, Sensitive Data Exposure, XXE, Broken Access Control, Security Misconfiguration, XSS, Insecure Deserialization.
- Asset Types: Web Application, Android Mobile App, iOS Mobile App, Infrastructure, Source Code, AI Model.

Текущий объем выборки:

- 2026 год, кварталы Q1 и Q2.
- 36 leaderboard views: 18 категорий на квартал.
- До 30 строк из каждой категории. В двух категориях HackerOne вернул меньше 30 строк: Q2 OWASP XXE - 20, Q2 Asset Type Infrastructure - 13.
- 1053 строки лидербордов до дедупликации.
- 610 уникальных usernames после дедупликации.
- 608 публичных профилей успешно обогащены; 2 профиля вернули ошибку `User does not exist`.
- 5342 публичных Hacktivity item сохранены в CSV как выборка активности за последний год.
- Суммарный публичный `total_count` Hacktivity по найденным пользователям: 8197.

Как получаются данные:

1. Скрипт открывает публичную страницу HackerOne и получает CSRF-токен.
2. Делает POST-запросы в `/graphql` с теми же публичными типами данных, которые использует веб-интерфейс.
3. Нормализует строки лидербордов.
4. Дедуплицирует usernames: если пользователь найден в нескольких категориях или кварталах, он остается одной записью `researcher`, а все его появления сохраняются в `leaderboard_entries`.
5. Обогащает пользователей публичными профилями.
6. Собирает публичную Hacktivity за последний год по каждому найденному username.
7. Считает производные scope-метрики и `standoff_priority_score`.
8. Сохраняет JSON и три CSV-таблицы.

CSV-таблицы:

- `data/hackerone_hunters_sample.csv` - одна строка = один уникальный исследователь.
- `data/hackerone_leaderboard_entries.csv` - одна строка = одно появление в лидерборде.
- `data/hackerone_hacktivity.csv` - одна строка = один публичный Hacktivity item.

Гиперссылки:

- CSV пишется с разделителем `;` и `UTF-8 with BOM`, чтобы Excel в русской локали корректно разделял колонки.
- `profile_url`, `website`, `github`, `twitter`, `linkedin`, `bugcrowd`, `gitlab`, `report_url`, `team_url` записываются как `=ГИПЕРССЫЛКА("url";"label")`.

Как учитываются ограничения платформы:

- Скрипт не требует логина и не обращается к приватным данным.
- Есть параметр `--limit`, чтобы ограничивать объем.
- Есть `--delay`, чтобы не отправлять частые запросы.
- Ошибки профилей не ломают весь сбор, а сохраняются в `metadata.profile_errors`.
- В боевой версии этот слой нужно заменить официальным API там, где есть токен и право доступа.

Почему не использован HTML-парсинг:

- Страницы HackerOne действительно загружаются через JavaScript, но сам фронтенд получает уже структурированные данные через GraphQL.
- Для тестового прототипа прямой GraphQL-запрос надежнее и проще проверяется, чем парсинг DOM после JS-рендера.
- Такой подход позволяет не зависеть от верстки страницы и работать с теми же публичными данными, которые использует веб-интерфейс.

Повторяемость и масштабируемость:

- Параметры года, квартала, лимита и типа пользователя вынесены в CLI.
- Лидерборды описаны декларативно через `LeaderboardSpec`.
- Добавление нового лидерборда требует добавить spec: key, GraphQL type, поля метрик и фильтр.
- Формат JSON сохраняет metadata, поэтому понятно, как именно была получена выборка.

## 5. Инструменты и стек

Использовано в тестовом:

- Python 3.13.
- Только стандартная библиотека: `urllib`, `json`, `csv`, `argparse`, `dataclasses`.
- JSON для структурированного результата.
- CSV для аналитической таблицы.
- Markdown для отчета.

Почему так:

- Нет внешних зависимостей, проект можно запустить сразу в текущем окружении.
- GraphQL-ответы уже структурированы, поэтому нет необходимости парсить HTML.
- JSON/CSV закрывают и машинную обработку, и ручную проверку результата.

Что использовал бы в боевой работе:

- Официальный HackerOne API с токеном, если есть договоренный доступ.
- Планировщик задач и хранилище: PostgreSQL + отдельная таблица raw snapshots.
- Очередь и rate limiting: Celery/RQ или managed scheduler.
- dbt/SQL-модели для производных признаков и витрин.
- Airflow/Prefect для регулярных прогонов.
- Валидация схемы через Pydantic и мониторинг изменений ответа.

## Формулы и скоринг

`standoff_priority_score` - не метрика HackerOne, а прикладной score для сортировки shortlist. Он нужен, чтобы не выбирать людей только по общей репутации.

Используется взвешенная сумма с ограничениями сверху:

```text
score =
  min(log10(reputation + 1) * 8, 40)
+ min(log10(valid_vulnerability_count + 1) * 7, 25)
+ min(signal * 2, 15)
+ min(impact, 15)
+ min(leaderboard_entries_count * 0.8, 18)
+ min(leaderboard_periods_count * 4, 8)
+ min(owasp_categories_count * 2, 12)
+ min(asset_type_categories_count * 2, 12)
+ min(high_critical_entries_count * 3, 12)
+ min(top_3_entries_count * 2, 10)
+ min(log10(hacktivity_total_count_last_year + 1) * 3, 10)
+ min(hacktivity_program_count * 1.5, 10)
+ cleared_bonus
+ verified_bonus
+ socials_bonus
```

Бонусы:

- `cleared_bonus = 2`, если профиль имеет `cleared`.
- `verified_bonus = 2`, если профиль имеет `verified`.
- `socials_bonus = 2`, если есть публичные внешние контакты.

Почему используется `log10` для reputation, valid vulnerabilities и Hacktivity:

- Эти признаки имеют длинный хвост: топовые аккаунты могут быть на порядки выше остальных.
- Логарифм сохраняет преимущество сильных исследователей, но не позволяет одному признаку полностью задавить остальные.
- Ограничения `min(..., cap)` делают score устойчивее и объяснимее для ручного анализа.

## 6. Результат

Артефакты:

- `data/hackerone_hunters_sample.json`
- `data/hackerone_hunters_sample.csv`
- `data/hackerone_leaderboard_entries.csv`
- `data/hackerone_hacktivity.csv`
- `main.py`
- `hackerone_research/collector.py`
- `hackerone_research/config.py`
- `hackerone_research/hackerone/`
- `hackerone_research/processing/`
- `hackerone_research/output/`

Топ исследователей в текущей выборке по производному `standoff_priority_score`:

| Username | Score | Reputation | Valid vulns | Наблюдаемые категории |
| --- | ---: | ---: | ---: | --- |
| m0chan | 163.62 | 125184 | 5287 | asset_web_app, high_critical, highest_reputation, most_upvoted, owasp_a2, owasp_a3, owasp_a4, owasp_a5, owasp_a6 |
| d0xing | 155.10 | 165219 | 5884 | asset_mobile_ios, asset_web_app, high_critical, highest_reputation, owasp_a1, owasp_a2, owasp_a5 |
| godiego | 153.15 | 86674 | 2469 | asset_web_app, high_critical, highest_reputation, most_upvoted, owasp_a1, owasp_a2, owasp_a7 |
| arielrachamim | 133.97 | 34045 | 2746 | asset_infrastructure, asset_mobile_ios, high_critical, highest_reputation |
| jayesh25 | 133.81 | 48913 | 1199 | asset_web_app, high_critical, highest_reputation, owasp_a2, owasp_a5 |
| n0xi0us | 133.53 | 21465 | 440 | asset_web_app, high_critical, highest_reputation, owasp_a4, owasp_a5, owasp_a7 |
| thaivu | 132.85 | 34058 | 1421 | asset_mobile_ios, asset_web_app, high_critical, highest_reputation, owasp_a2, owasp_a7 |
| mister_mime | 131.90 | 12233 | 258 | asset_source_code, high_critical, highest_reputation, owasp_a1, owasp_a2, owasp_a3, owasp_a8 |

Наблюдения:

- Наиболее интересные кандидаты не всегда просто "первые по общей репутации". Более полезный shortlist получается, когда учитываются профильные лидерборды и повторяемость в нескольких категориях.
- Web App, High/Critical, OWASP и Mobile/Infra категории дают более прикладной сигнал для багбаунти-платформы, чем общий топ.
- Most Upvoted Hacktivity добавляет отдельный сигнал публичной заметности: такие исследователи могут быть полезны для community-building, write-ups и амбассадорских активностей.
- Up and Comers полезен для отдельной стратегии привлечения: это не всегда самые опытные участники, но они могут быть активнее и доступнее для ранней коммуникации.
- Наличие внешних хендлов и верификации помогает разделять кандидатов по процессам: публичное приглашение, приватная программа, pentest/enterprise-сценарий.
- Годовая Hacktivity помогает отделить исторически сильные аккаунты от тех, кто продолжает регулярно взаимодействовать с программами.

Идеи применения для Standoff:

- Shortlist для приглашений в приватные программы по специализациям: Web App, Mobile, Infrastructure, OWASP, High/Critical.
- Сегментация исследователей: elite, specialist, rising, community-visible.
- Подбор исследователей под scope программы, а не только по общей репутации.
- Персонализированные приглашения: ссылаться на категорию, где исследователь силен.
- Отдельная воронка для Up and Comers с обучением, челленджами и быстрыми первыми выплатами.
- Внутренний скоринг для program managers: кого приглашать первым, кого держать в nurturing-списке, кому предлагать приватные scope.

## Что улучшить при продолжении

- Добавить историю за большее число кварталов и смотреть динамику ранга.
- Сопоставлять HackerOne-профили с Bugcrowd, GitHub, LinkedIn и публичными write-ups.
- Добавить контроль изменений схемы GraphQL.
- Хранить raw responses для воспроизводимости и аудита.
- Разделить scoring-модель на конфиг, чтобы веса можно было обсуждать с бизнесом.
