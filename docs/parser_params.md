# parser_params

S2-выгрузка параметров и контрактов из `legacy/`.

## Что вошло

- CLI: `legacy/generate_dashboard.py`
- entrypoint: `legacy/main.py`
- конфиг: `legacy/src/config.py`
- основной Yandex-парсер: `legacy/src/parsers/yandex_parser.py`
- детальный парсер: `legacy/src/parsers/single_parser.py`
- варианты Yandex-ветки: `legacy/targeted_parser.py`, `legacy/scrolling_parser.py`, `legacy/universal_parser.py`
- Ozon-ветка и браузерные дефолты: `legacy/src/parsers/ozon_parser.py`, `legacy/src/parsers/ozon_parallel_parser.py`

## Ключевые параметры

| Name | Type | Default | Group | UI | Editable | Advanced | Source |
|---|---|---:|---|---|---|---|---|
| `search_url` | string | URL поиска Yandex Maps | entrypoint | text | yes | no | `legacy/src/config.py:8-9` |
| `target_businesses_count` | number | `0` | limits | number | yes | no | `legacy/src/config.py:11-12` |
| `target_products_count` | number | `50` | limits | number | yes | no | `legacy/src/config.py:14-15` |
| `delays.page_load` | number | `5` | timing | number | yes | no | `legacy/src/config.py:17-24` |
| `browser.window_size` | string | `1920,1080` | browser | text | yes | yes | `legacy/src/config.py:26-32` |
| `browser.disable_logging` | boolean | `true` | browser | checkbox | yes | yes | `legacy/src/config.py:26-32` |
| `logging.level` | string | `INFO` | logging | select | yes | no | `legacy/src/config.py:41-46` |
| `save.save_json` | boolean | `true` | output | checkbox | yes | no | `legacy/src/config.py:48-54` |
| `error.max_retries` | number | `3` | recovery | number | yes | yes | `legacy/src/config.py:56-61` |
| `ozon.browser.user_agent` | string | Chrome 120 UA | browser | text | yes | yes | `legacy/src/config.py:87-94` |
| `main.session_name` | string | `null` -> auto `parsing_YYYYMMDD_HHMMSS` | entrypoint | text | yes | no | `legacy/main.py:21-31` |
| `generate_dashboard.output` | string | `null` | cli | text | yes | no | `legacy/generate_dashboard.py:19-30,87-94` |
| `generate_dashboard.open` | boolean | `false` | cli | checkbox | yes | no | `legacy/generate_dashboard.py:19-30,114-119` |
| `single.session_folder` | string | `parsing_results/businesses` | storage | text | yes | no | `legacy/src/parsers/single_parser.py:24-31` |
| `single.max_products` | number | `10` | limits | number | yes | no | `legacy/src/parsers/single_parser.py:24-31` |
| `single.find_element_by_selectors_with_timeout.timeout` | number | `10` | timing | number | yes | yes | `legacy/src/parsers/single_parser.py:592-610` |
| `universal.headless` | boolean | `false` | browser | checkbox | yes | yes | `legacy/universal_parser.py:24-33,64-65` |
| `universal.link_limit` | number | `50` | limits | number | yes | yes | `legacy/universal_parser.py:194-219` |
| `targeted.target_count` | number | `20` | limits | number | yes | no | `legacy/targeted_parser.py:24-33,537-547` |
| `scrolling.target_count` | number | `20` | limits | number | yes | no | `legacy/scrolling_parser.py:502-523` |
| `ozon_parallel.headless` | boolean | `false` | browser | checkbox | yes | yes | `legacy/src/parsers/ozon_parallel_parser.py:23-50` |
| `ozon_integrated.wait_timeout` | number | `30` | timing | number | yes | yes | `legacy/src/parsers/ozon_parser.py:47-76` |

## Селекторы

Селекторы вынесены в draft как `selector[]` и помечены `editable=false`, `advanced=true`. Это включает:

- контейнеры и ссылки выдачи Яндекс Карт;
- селекторы названия, адреса, категорий, телефона и сайта предприятия;
- вкладки и карточки товаров/услуг;
- альтернативные контейнеры и кликабельные элементы в targeted/scrolling вариантах;
- Ozon-селекторы карточки, детальной страницы, цены, рейтинга, отзывов и доставки.

## Извлекаемые поля предприятия

Основной контракт данных предприятия подтверждён в `legacy/targeted_parser.py` и совпадает с более ранними вариантами `scrolling_parser.py` и `single_parser.py`.

| Field | Type | Default | Source |
|---|---|---|---|
| `business.name` | string | `""` | `legacy/targeted_parser.py:257-313,326-338` |
| `business.verified` | boolean | `false` | `legacy/targeted_parser.py:331-336` |
| `business.categories` | array | `[]` | `legacy/targeted_parser.py:340-345` |
| `business.rating` | string | `""` | `legacy/targeted_parser.py:347-352` |
| `business.reviews_count` | string | `""` | `legacy/targeted_parser.py:354-362` |
| `business.awards` | array | `[]` | `legacy/targeted_parser.py:364-369` |
| `business.address` | string | `""` | `legacy/targeted_parser.py:371-380` |
| `business.phones` | array | `[]` | `legacy/targeted_parser.py:382-387` |
| `business.website` | string | `""` | `legacy/targeted_parser.py:389-394` |
| `business.social_links` | object | object with `whatsapp/vk/instagram/facebook/telegram/ok/youtube/other` | `legacy/targeted_parser.py:396-414` |
| `business.working_hours` | object | `{current_status:"", schedule:[]}` | `legacy/targeted_parser.py:416-424` |
| `business.services` | array | `[]` | `legacy/targeted_parser.py:426-431` |
| `business.products` | array | `[]` | `legacy/targeted_parser.py:442-449` |
| `business.prices` | array | `[]` | `legacy/targeted_parser.py:442-449` |
| `business.features` | array | `[]` | `legacy/targeted_parser.py:435-439` |
| `business.has_panorama` | boolean | `false` | `legacy/targeted_parser.py:442-447` |
| `business.stories` | array | `[]` | `legacy/targeted_parser.py:449-454` |
| `business.coordinates` | object | `{lat:"", lon:""}` | `legacy/targeted_parser.py:257-313` |
| `business.yandex_id` | string | `""` | `legacy/targeted_parser.py:456-463` |
| `business.url` | string | `""` | `legacy/targeted_parser.py:292-301` |
| `business.last_updated` | string | `datetime.now().isoformat()` | `legacy/targeted_parser.py:279-313` |

## Замечания

- Отдельных `os.getenv(...)` / `os.environ[...]` параметров в `legacy/*.py` не найдено.
- Отдельной proxy-конфигурации в активных парсерах не найдено; есть только пример в архивном коде `legacy/_trash/example.py`.
- `user-agent` подтверждён в Ozon-парсерах и универсальном парсере.
