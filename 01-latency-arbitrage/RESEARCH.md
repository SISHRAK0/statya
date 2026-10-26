# RESEARCH: латентный арбитраж на краткосрочных крипторынках Polymarket

*Состояние на 2026-10-26. Метки уверенности: **[В]** высокая (первичный источник или наша проверка через API), **[С]** средняя (несколько вторичных источников или косвенный вывод), **[Н]** низкая / «не подтверждено».*

Часть фактов проверена напрямую: 26.10.2026 мы запросили Gamma API (`gamma-api.polymarket.com/events?slug=…`) по серии `btc-updown-{5m,15m}-{unix_ts}` на разные даты и прочитали поля `description`, `feeType`, `feeSchedule`, `feesEnabled`. Такие факты помечены «(API)».

---

## 1. Механика продукта

### 1.1. Линейка рынков и даты запуска

| Серия | Старт | Источник разрешения | Уверенность |
|---|---|---|---|
| 15 мин (BTC, ETH, SOL, XRP; сейчас также DOGE, BNB, HYPE, ZEC; есть XAU/XAG 15m) | анонс с Chainlink 12.09.2025; первый рынок `btc-updown-15m` ≈ **09.10.2025** (бинпоиск по API; та же дата у Dai–Jia–Yu) | Chainlink Data Streams (до 07.08.2026 цена в момент, после — TWAP) | [В] |
| 4 часа | 15.10.2025 (Dai–Jia–Yu) | Chainlink; с 07.08.2026 TWAP 60 с | [С] |
| 5 мин | контракт создан в 12.2025; публичный запуск **12.02.2026** (changelog; в прессе 13.02) | Chainlink; с 07.08.2026 TWAP 30 с, с 14.08.2026 TWAP 60 с | [В] |
| 1 час (`bitcoin-up-or-down-<date>-<h>-et`) | существовал уже в 10.2025 | **Binance BTC/USDT, свеча 1H, close ≥ open** — не Chainlink | [В] (API) |
| Дневной | — | Binance BTC/USDT, close 1-минутной свечи 12:00 ET против предыдущего дня | [В] (API) |

Формулировка правил 15-минутного рынка до 07.08.2026: «Up, если цена в конце интервала ≥ цены в начале… источник — Chainlink BTC/USD data stream… а не другие источники или спот» (API). С 07.08.2026: «Up, если TWAP Bitcoin от Chainlink за интервал ≥ цены в начале интервала», источник `data.chain.link/streams/btc-usd-twap-60s-streams` (API; changelog 07.08.2026: «Crypto up/down markets now resolve using Chainlink-computed time-weighted average prices… lookback 30 s for 5-min, 60 s for 15-min and 4-hour»). Цена открытия по changelog тоже берётся из TWAP-фида. [В]

Отсюда **две разные архитектуры оракула**. У 5m/15m/4h это Chainlink: оракул агрегирует биржи и отстаёт от Binance на ~1,6–2 с по наблюдениям практиков [Н]. У 1H/дневных это сама свеча Binance. Сравнение двух архитектур полезно для дизайна исследования.

Расчёт автоматический: `automaticallyResolved=true`, UMA не участвует. `closedTime` наступает примерно через 80 с после конца окна (API, пример 26.10.2026). После конца окна, но до резолюции, ещё идут сделки по 0.999/0.001 (data-api). Их нужно отфильтровывать. [В]

### 1.2. CLOB и задержка тейкера

- Гибридный CLOB: матчинг офчейн у оператора, расчёт ончейн на Polygon, атомарно через settlement-контракт (docs «Order lifecycle»). [В]
- 28.04.2026 запущен **CLOB V2**: новые exchange-контракты, коллатерал pUSD вместо USDC.e, переделанное событие `OrderFilled` (один `tokenId`, явный `side`, builder-атрибуция), в ордере метка `timestamp` в мс вместо nonce. Встречаются даты 22.04 и 28.04. В списке контрактов уже есть `ExchangeV3 Poly v2`, так что набор адресов менялся не один раз. [С]
- 24.07.2026 «async commit pipeline cuts matching latency», после чего FAK/FOK перестали возвращать `transactionHashes` (changelog). [В]
- **Taker delay (speed bump)** на «selected crypto and finance up/down markets»: тейкерский ордер удерживается, потом проходит повторную валидацию. С 05.06.2026 ордер в окне задержки нельзя отменить. По changelog: 250 мс → **50 мс с 17.08.2026 11:00 UTC** → **150 мс с 04.09.2026 14:00 UTC**. Страница order-lifecycle до сих пор пишет 250 мс. Флаг задержки виден в `GET /clob-markets/{condition_id}`. [В] по датам changelog; **дата введения задержки не подтверждена** [Н].
- Шаг цены 0.001, минимальный ордер 5 шейров (API). По OpenMarket, в BTC 15m 91,9% наблюдений спред равен одному тику (0.01 на их данных). [С]

### 1.3. Комиссии и ребейты

История по полю `feeSchedule` в API (рынки BTC 15m, 14:00 UTC каждой даты):

| Период | feeType | feeSchedule | Комиссия на 1 шейр | При p=0.5 |
|---|---|---|---|---|
| до 06.01.2026 | — | нет, `feesEnabled=false` | 0 | 0 |
| 07.01 – ~05.03.2026 | `crypto_15_min` | rate 0.25, exponent 2 | 0.25·[p(1−p)]² | 1.56 ¢ (3.1% номинала) |
| ~05.03 – 30.03.2026 | `crypto_fees` | то же | то же | то же |
| с 30/31.03.2026 | `crypto_fees_v2` | rate 0.07, exponent 1 | 0.07·p(1−p) | 1.75 ¢ (3.5% номинала) |

- Формула для первого периода восстановлена по примерам в прессе: 100 шейров по $0.50 дают $1.56, по $0.10 дают $0.20, по $0.99 дают $0.0025 (Cointelegraph, DeFi Rate). Это совпадает с 0.25·[p(1−p)]² и **не** совпадает с записью «C·p·feeRate·(p(1−p))^exp» в нескольких гайдах. Changelog 05.01.2026: «peak 1.56% at 50% probability», то есть на $1 выплаты. Комиссии включены 05–07.01.2026, первой это заметила пресса 06.01. [В] по параметрам API, [С] по точной форме формулы до V2.
- Текущая формула из docs: `fee = C × feeRate × p × (1 − p)`, crypto feeRate = 0.07, мейкер не платит. В таблице docs 100 шейров по $0.50 стоят $1.75. [В] Цифра «1.80%» из Benzinga/KuCoin возможно отражает промежуточное значение 0.072 [Н].
- 06.03.2026 комиссии распространены на 1H/4H/дневные/недельные крипторынки, созданные после 06.03 (changelog). 30.03.2026 введён Fee Structure V2 по всем категориям, кроме геополитики. С 31.03 комиссию считают по `feeSchedule` рынка. [В]
- **Ребейты мейкерам**: пул равен 20% тейкерских комиссий в крипто (`rebateRate: 0.2`). Пул делится внутри каждого рынка пропорционально «fee-equivalent» мейкерских филлов, выплата ежедневно в pUSD, порог $1, процент «at the sole discretion of Polymarket» (docs Maker Rebates). [В] Поле `makerRebatesFeeShareBps=10000` и легаси-поля `takerBaseFee/makerBaseFee=1000` (их же возвращает `/fee-rate`) ни на что не указывают. Их смысл **не подтверждён** [Н]. Брать их за реальную ставку нельзя.
- Мотив. Официально комиссия финансирует ребейты и ликвидность (The Block, Cointelegraph). Finance Magnates прямо называет цель «нейтрализовать латентный арбитраж», который появился при нулевых комиссиях. Явной цитаты Polymarket про latency arbitrage мы **не нашли** [Н].

### 1.4. Масштаб

С 15.02 по 30.03.2026 у 5m-рынков $2,3 млрд номинала, у 15m $795 млн. Доля «быстрых» рынков в криптообъёме выросла с ~40% (09.2025) до >80% (03.2026), BTC около 77% (Dune blog, сейчас 404, цитата по поисковой выдаче) [С]. Bloomberg через PYMNTS: до $60 млн в день [С]. Telonex за 2–8.02.2026 по 2 688 рынкам 15m насчитал 15,3 млн филлов, $153 млн, 46 945 кошельков. До комиссий мейкеры заработали +$728 501, тейкеры потеряли столько же. [С]

---

## 2. Литература

### 2.1. Латентный арбитраж и HFT (ядро)
- **Budish, Cramton, Shim (2015, QJE)**, «The High-Frequency Trading Arms Race: Frequent Batch Auctions as a Market Design Response». Механические арбитражные возможности при непрерывном аукционе; снайпинг стейл-котировок как налог на ликвидность; batch auctions.
- **Aquilina, Budish, O'Neill (2022, QJE)**, «Quantifying the High-Frequency Trading Arms Race». Гонки по сообщениям LSE: около 20% объёма, «latency arbitrage tax» около 0,42 б.п. Методология определения «гонок» переносится на наш случай почти напрямую.
- **Foucault, Kozhan, Tham (2017, RFS)**, «Toxic Arbitrage». Арбитраж на стейл-котировках ухудшает ликвидность. Ближайший теоретический аналог.
- **Menkveld, Zoican (2017, RFS)**, «Need for Speed? Exchange Latency and Liquidity»; **Baldauf, Mollner (2020, JF)**, «High-Frequency Trading and Market Performance»; **Shkilko, Sokolov (2020, JF)**, «Every Cloud Has a Silver Lining».
- Speed bumps: **Chen, Foley, Goldstein, Ruf (2017+)** про TSX Alpha; **Brolley, Cimon (2020, JFQA)**, «Order-Flow Segmentation, Liquidity, and Price Discovery: The Role of Latency Delays»; **Aldrich, Friedman** про IEX. Прямая теория для нашего taker delay.
- Классика adverse selection: Glosten–Milgrom (1985), Kyle (1985).

### 2.2. LVR и AMM
- **Milionis, Moallemi, Roughgarden, Zhang (2022)**, «Automated Market Making and Loss-Versus-Rebalancing» (arXiv 2208.06046). LVR = σ²/2 · (кривизна) · dt.
- **Milionis, Moallemi, Roughgarden (2023)**, «Automated Market Making and Arbitrage Profits in the Presence of Fees». Вероятность арбитража при дискретных блоках и комиссии. Это аналог нашего «порога» из fee + задержки.
- **Moallemi, Robinson, Zhu (2026)**, «Uniform-Loss Automated Market Making for Prediction Markets» (arXiv 2607.17428). LVR для бинарных рынков на win-martingale: LVR это одновременно потери LP и субсидия информированным. Самая близкая работа к «LVR для бинарного контракта». Для CLOB её надо переписывать в терминах стейл-лимиток.

### 2.3. Рынки предсказаний: эффективность и микроструктура
- **Wolfers, Zitzewitz (2004, JEP)**, «Prediction Markets»; (2006) про интерпретацию цен как вероятностей.
- **Bürgi, Deng, Whelan (2025/26)**, «Makers and Takers: The Economics of the Kalshi Prediction Market» (CESifo / CEPR DP20631 / GWU WP 2026-001). Мейкеры зарабатывают больше тейкеров; favourite–longshot bias.
- **Saguillo, Ghafouri, Kiffer, Suarez-Tangil (2025)**, «Unravelling the Probabilistic Forest: Arbitrage in Prediction Markets» (arXiv 2508.03474, AFT 2025). Около $40 млн арбитражной прибыли на Polymarket за 04.2024–04.2025, в основном межрыночный и внутрирыночный (сумма цен ≠ 1). **Не латентный.**
- **Gebele, Mutzel, Matthes (2026)**, «Executable Arbitrage and Market Efficiency in Prediction Markets» (arXiv 2608.00666). Neg-risk-арбитраж, около $1,12 млн.
- **Dubach (2026)**, «The Anatomy of a Decentralized Prediction Market: Microstructure Evidence from the Polymarket Order Book» (arXiv 2604.24366, SSRN 6658364). 30 млрд событий стакана, 52 дня (21.02–15.04.2026), топ-100 рынков. Компонента adverse selection по Glosten–Harris около нуля. Знак сделки из фида совпадает с ончейном **только в ~59%**. Задержка ингеста меньше 50 мс в медиане с хвостом в секунды. Крипто-up/down специально не изучает.
- Арбитраж в NBA-рынках (arXiv 2605.00864): опрос раз в 3,6–5,5 с, короткие эпизоды не ловятся. Хороший пример ограничения.
- Lejmi (2026, arXiv 2610.26789): MARL-маркетмейкинг на стаканах рынков предсказаний.

### 2.4. Прямо про краткосрочные крипторынки Polymarket (критично для новизны)
1. **Dai, Jia, Yu (2026)**, «Settlement Manipulation in Prediction Markets» (arXiv 2606.31675; Stanford/SMU). Около 16 тыс. 5m BTC-контрактов. Order flow на Binance в последние 10 с растёт на ~50% после запуска 5m. 821 кошелёк, ~$8,2 млн, 93% потерь у ритейла. На 15m эффект слабый. В модели мейкер получает ренту, глубина Polymarket после near-even закрытий падает. Тема манипуляции, а не латентности, но после этой работы Polymarket перешёл на TWAP. **Основная работа, с которой нас будут сравнивать.**
2. **Young (2026)**, «OpenMarket: A Synchronized Polymarket–Binance Dataset for High-Frequency Prediction-Market Research» (arXiv 2607.26245). BTC 15m + Binance BTCUSDT, 54 дня (12.02–15.05.2026), 727 млн строк, мс-метки. Lead–lag по часам источников даёт медиану **16 мс** (p5/p95: −186/316), с неразрешимым константным сдвигом ±99 мс. Event study на скачках Binance ≥5 б.п. даёт **медиану 347 мс** до сдвига котировки Polymarket на тик. Модель не обгоняет mid рынка. Латентный арбитраж и потери мейкеров **не изучаются**. Ближайший датасет и прямой конкурент по измерению лага.
3. **Практик-отчёт GitHub `Yak0vkaSup/polymarket-microstructure`** (07–09.2026, самоотчёт, [Н]). Оракул отстаёт от Binance на ~1,65 с. Тейкер-снайпинг после комиссий около нуля (t = −0,05). «Winner's curse» на филлах. Средний мейкер BTC 5m +0,275 ¢/шейр нетто (95% ДИ [0,15; 0,40]). Филлы после неблагоприятного движения Binance за предыдущие 3 с: −1,32 ¢, без движения +0,93 ¢. Бэктест мейкера неидентифицируем по публичной ленте: сдвиг матчинга на 150 мс меняет знак. По сути это неформальная версия нашей статьи. **Высокий риск для новизны, но и готовые гипотезы.**
4. Telonex research (02.2026): PnL кошельков 15m, архетипы «снайперы» и «MM-боты». Без анализа латентности.
5. Медиа и блоги: Finance Magnates (бот $313 → $414k за месяц, 98% винрейт, источник один твит 05.01.2026 [Н]); Medium/Indie Hackers/QuantVPS/dev.to (лаги «2–30+ с», «30–90 с», «12,3 → 2,7 с»; всё [Н], часто маркетинг ботов); много open-source ботов на GitHub.

**Итог по новизне.** Факт лага и его порядок (сотни мс в котировках, около 1,5–2 с у оракула) уже опубликован (OpenMarket, практики). Причинной оценки того, **как комиссии, speed bump и TWAP перераспределили ренту между снайперами и мейкерами**, мы не нашли ни в академическом, ни в практическом виде. Это и есть ниша.

---

## 3. Данные

### 3.1. Polymarket
| Источник | Что даёт | Точность времени | Подводные камни |
|---|---|---|---|
| Gamma API (`gamma-api.polymarket.com`) | метаданные рынков, правила, `feeSchedule`, `eventStartTime`, `closedTime`, tokenIds | — | слаги детерминированы (`{asset}-updown-{5m,15m,4h}-{unix_start}`); удобно для полной выборки |
| data-api (`/trades?market=`) | сделки с кошельком (proxyWallet), side, price, size, txHash | **секунды** | только тейкерская сторона, есть пагинация и лимиты; сделки после окна |
| CLOB REST (`/book`, `/prices-history`) | текущий стакан; история mid | `/prices-history` с шагом ≥1 мин | **исторического стакана нет**, после закрытия `/book` даёт «No orderbook exists» (проверено) |
| CLOB WebSocket (market channel) | L2-апдейты, `price_change`, `last_trade_price` | мс (серверная метка) | писать самим и в реальном времени; дропы и дрейф часов (OpenMarket, Dubach) |
| RTDS / PolyBolt (`ws-live-v2.polymarket.com`) | цены Binance и Chainlink, с 15.09.2026 Chainlink TWAP reference | мс | RTDS legacy с 15.09.2026; источник `pyth`/`chainlink` в поле `source` |
| Ончейн Polygon: `OrderFilled`/`OrdersMatched` на CTF Exchange (v1 до ~28.04.2026; V2 `0xE111…996B`, Neg Risk V2 `0xe222…0F59`, ExchangeV3) | все филлы с maker/taker адресами, fee | время блока (~2 с), порядок по logIndex | смена ABI и адресов в V2; время блока ≠ время матчинга (матчинг офчейн); сторонние схемы отстают от апгрейдов |
| Dune (запросы 6545441 и др., дашборды hildobby/datadashboards), Goldsky, CryptoHouse (ClickHouse), Allium, substreams `polymarket` | агрегаты и сырые ончейн-филлы | блок | проверить, что таблицы покрывают V2-контракты |
| Готовые архивы | OpenMarket (Young), архив Dubach | мс | условия доступа и покрытие (только BTC 15m, 02–05.2026) **не подтверждены** [Н] |

Ключевая проблема: **ни один публичный источник не даёт историю стакана с мс до 2026 года**. Значит, (а) свой рекордер вперёд и/или (б) чужие архивы (OpenMarket, Dubach, коммерческие вроде Telonex и PolymarketData, условия [Н]), (в) для истории только ончейн-филлы с точностью до блока.

### 3.2. Спот и оракул
- **Binance**: WebSocket `trade`/`aggTrade`/`bookTicker` (метки в мс; для спота доступны микросекунды через параметр timeUnit [С]). История на `data.binance.vision`: trades/aggTrades, для спота с 2025 года в микросекундах [С]. `bookTicker` исторически не публикуется, нужен свой сбор или Tardis.dev.
- **Coinbase** Advanced Trade WS (ISO-метки с мкс), **Tardis.dev** (нормализованный L2 по многим биржам с локальной меткой получения, платно).
- **Chainlink Data Streams**: отчёты с `observationsTimestamp` (секунды). Доступ к API требует ключей (платно/по договорённости). Публичная история на data.chain.link для BTC/USD и TWAP-60s в нужной детализации **не подтверждена** [Н]. Практичный обходной путь: писать RTDS/PolyBolt (Polymarket ретранслирует Chainlink) или восстанавливать цены открытия и закрытия из исходов рынков.
- **CF BRTI** (Kalshi): для кросс-платформенного сравнения. Kalshi 15m считается по 60-секундному среднему BRTI [С].

### 3.3. Подводные камни
1. Часы: дрейф и константный сдвиг между площадками. Одна точка сбора не разрешает ±100 мс (OpenMarket). Нужна колокация в AWS ap-northeast-1 (Binance) и в регионе Polymarket (по слухам eu-west/London [Н]) или по крайней мере NTP/PTP и оценка транспортной задержки.
2. Знак сделки из фида ненадёжен (59% по Dubach), его надо брать из ончейна.
3. Мейкерский PnL чувствителен к неизвестному моменту матчинга: сдвиг на 150 мс меняет знак (практик-отчёт). Нужны оценки в виде границ (bounds), а не точечные.
4. Режимы: комиссии (01/03.2026), V2 (04.2026), async matching (24.07), TWAP (07/14.08), delay 250 → 50 → 150 (17.08 / 04.09). Каждую выборку нужно размечать по режиму.
5. Фильтровать сделки после окна и до резолюции, а также ребейты, которые выплачиваются вне филлов.

---

## 4. Методология

### 4.1. Измерение лага
- **Hayashi–Yoshida** кросс-ковариация на несинхронных тиках и оценка lead–lag параметра **Hoffmann–Rosenbaum–Yoshida (2013)** по сетке сдвигов; **Huth–Abergel (2014)** LLR (lead-lag ratio). Цена Polymarket переводится в «подразумеваемый спот» через обратную бинарную формулу (Φ⁻¹ от mid с σ, оценённой bipower variation), либо, наоборот, «справедливая вероятность» считается из спота: P(Up) = Φ(ln(S_t/S_0)/(σ√τ)) с поправкой на TWAP после 07.08.
- **Event study на скачках спота**: скачки Binance ≥ k б.п. за ≤100 мс (Lee–Mykland / порог по bipower), окна ±2 с. Метрики: время до первого изменения котировки или отмены на Polymarket, время до первой тейкерской сделки в направлении скачка, доля стейл-уровней, снятых тейкером, против отменённых мейкером. Это прямой аналог «гонок» Aquilina–Budish–O'Neill: группа сообщений (take/cancel) на одном ценовом уровне в течение Δ после триггера.
- **Information share** (Hasbrouck 1995) и **Dobrev–Schaumburg** cross-market activity как устойчивые альтернативы.

### 4.2. Прибыль арбитражёра и потери мейкеров
- **Markout / realized spread**: для каждого мейкерского филла считаем PnL против «справедливой вероятности» из спота через h ∈ {100 мс, 1 с, 5 с, 30 с} и против итогового исхода. Потери мейкеров от снайпинга определяем как markout на филлах внутри окна гонки. Получается аналог LVR: **«loss-versus-fair-value» = Σ (p_fair,t+h − p_fill)·q·sign**.
- Теоретический бенчмарк: стейл-котировка на бинарном контракте теряет при скачке спота ΔS величину ≈ φ(d)/(σ√τ)·ΔS/S. «Гамма» бинарника растёт к экспирации, поэтому **ожидаемые потери мейкера от лага Δ растут как 1/√τ** в конце окна. Это проверяемый прогноз, и это естественный мост к LVR (σ²·кривизна) у Milionis et al. и Moallemi–Robinson–Zhu.
- Декомпозиция ренты: валовый снайпинговый доход = комиссия + ребейт мейкеру (20% комиссии) + чистый доход снайпера + потери мейкера. Комиссия 0.07·p(1−p) задаёт порог неактивности. Арбитраж невыгоден, если |p_fair − p_quote| < fee(p). Это даёт **«no-trade band», зависящий от p**, и его форму можно проверить на данных.

### 4.3. Идентификация арбитражных адресов
- Ончейн: тейкер-адрес (proxyWallet / Safe). Признаки: доля тейкерских филлов, условная частота сделок через ≤ X мс/блок после скачка Binance, направление совпадает со скачком, положительный markout на коротком горизонте и около нуля дальше, работа 24/7, равномерный размер. Кластеризация (k-means/GMM) и устойчивость к порогам.
- Связывание кошельков: общий фондер USDC/pUSD, общие операторы Safe, builder-атрибуция в V2 `OrderFilled`.
- Ограничение: кошелёк ≠ субъект. Это стандартная оговорка (Telonex, Dai–Jia–Yu).

### 4.4. Идентификация причинности (главная ценность)
Режимные изменения как квази-эксперименты, DiD с контрольной группой:
1. **05–07.01.2026 комиссии на 15m**, контроль: 1H/4H (без комиссий до 06.03). Влияние на частоту гонок, markout мейкеров, спреды и глубину.
2. **06.03.2026 комиссии на 1H/4H**: обратный дизайн.
3. **30.03.2026 смена формы кривой** (exp 2 → 1, пик 1,56 → 1,75 ¢). Комиссия заметно выросла на хвостах p (при p=0.1 с 0,20 ¢ до 0,63 ¢). Тест «no-trade band по p».
4. **07.08 / 14.08.2026 TWAP**: снайпинг в последние секунды теряет смысл. Ожидаем сдвиг активности от экспирации в середину окна и снижение «гаммы» конца окна.
5. **Speed bump 250 → 50 → 150 мс** (17.08, 04.09.2026): почти чистый эксперимент про задержку как защиту мейкеров (Brolley–Cimon, Baldauf–Mollner). Практики сообщают, что при 50 мс объём упал [Н].
6. Кросс-секция: BTC против альткоинов (разная ликвидность оракула), 5m против 15m против 1H (Chainlink против Binance-свечи).

---

## 5. Новизна и риски

### 5.1. Что уже сделано
- Лаг котировок к Binance: OpenMarket (347 мс в event study; 16 мс как «apparent» lead–lag).
- Манипуляция расчётом на 5m: Dai–Jia–Yu.
- Общая микроструктура Polymarket и adverse selection около нуля в топ-100: Dubach.
- Неформальные измерения лага оракула (~1,65–2 с), прибыльности мейкеров и снайперов, влияния speed bump: практик-отчёт на GitHub.
- PnL кошельков 15m: Telonex.

### 5.2. Возможный вклад (кроме «задержка есть»)
1. **Перераспределение благосостояния**: доля ренты латентного арбитража у снайперов, мейкеров, платформы (комиссия минус ребейт) и рефералов; как она менялась по режимам. Аналог Aquilina et al. для рынка предсказаний.
2. **Причинный эффект трёх инструментов дизайна**: ценовой (комиссия p(1−p)), временной (speed bump), контрактный (TWAP). Их сравнительная эффективность для защиты мейкеров и стоимость для тейкеров-неарбитражёров. Прямо продолжается в темы [04](../04-optimal-taker-fees/) и [05](../05-mitigating-latency-arbitrage/).
3. **Теория LVR для бинарного CLOB**: потери мейкера ~ гамма бинарника × лаг, рост к экспирации, no-trade band от p(1−p). Эмпирическая проверка формы.
4. **Двухслойная латентность**: «спот → оракул» (Chainlink около 1,5–2 с) и «спот → котировка» (сотни мс). Аргумент, что рынок предсказаний с оракулом это рынок с **известным будущим отчётом**, и это отличает его от классического латентного арбитража на акциях.
5. **Методический вклад**: границы (bounds) на мейкерский PnL при неизвестном моменте матчинга; валидация ончейн против фида.

### 5.3. Риски
- **Восприятие как торговой стратегии.** Это главный риск, пользователь его уже отметил. Как снизить:
  - писать в терминах welfare и market design, с исследовательским вопросом «кто платит за лаг и помогают ли комиссии/speed bump/TWAP»;
  - давать агрегаты по режимам и кросс-секции, а не правила входа: никаких порогов сигналов, конкретных параметров ботов, инфраструктурных рецептов вроде «колоцируйся в X», PnL по рецепту;
  - основной период анализа брать **до** текущих правил (до 07.08 и 04.09.2026), где стратегии уже неактуальны, а текущий режим описывать только агрегатно;
  - не публиковать адреса кошельков (анонимизировать, только классы); код выкладывать для измерений, а не для торговли;
  - заранее упомянуть, что результаты устарели из-за изменений дизайна (это правда и усиливает тезис о «design response»).
- **Конкуренция и устаревание**: OpenMarket и Dai–Jia–Yu уже покрывают соседнюю территорию, а Polymarket меняет правила каждые 1–2 месяца. Ответ: позиционировать статью как исследование естественных экспериментов, которые как раз и создают эти изменения.
- **Данные**: без исторического стакана с мс полноценное event study возможно только на чужих архивах или на данных, собранных вперёд. Ончейн даёт только блок (~2 с), и это больше измеряемого лага.
- **Юридический и репутационный риск** платформы: публичные упоминания кошельков, нарушение ToS API (rate limits).

---

## 6. Вердикт

- **Реализуемость: 3/5.** Метаданные, режимы, ончейн-филлы и data-api доступны бесплатно и сразу (проверено). Узкое место — **мс-история стакана и оракула до 2026**. Без доступа к архиву OpenMarket или Dubach (или коммерческому) первая версия работает на ончейн-филлах с точностью до блока плюс собственный рекордер с сегодняшнего дня. Режимы 2026 года в прошлом, вперёд их уже не собрать.
- **Новизна: 3/5** при фокусе «лаг существует» это скорее 2/5. **4/5** при фокусе на причинном анализе инструментов дизайна (fee curve, speed bump, TWAP) и декомпозиции благосостояния.

**Что нужно для старта**
1. Скрипт выгрузки всех 5m/15m/1H/4H рынков (Gamma по детерминированным слагам) с `feeSchedule`, правилами и временем; таблица режимов.
2. Ончейн-филлы V1+V2 (Dune/Goldsky/substreams), сверка с data-api.
3. Binance trades/aggTrades с data.binance.vision за 10.2025–10.2026; Tardis для bookTicker при бюджете.
4. Запрос архивов: OpenMarket (Young), Dubach. Проверить условия Telonex/PolymarketData/Allium.
5. Рекордер с сегодняшнего дня: WS стакана Polymarket + PolyBolt (Chainlink TWAP) + Binance bookTicker на синхронизированных часах. Это для текущего режима 150 мс/TWAP и для валидации.
6. Сверить библиографию: выходные данные Budish et al., Aquilina et al., Foucault et al., Brolley–Cimon и др. приведены по памяти.

**Рекомендуемая структура статьи**
1. Introduction: рынки с оракулом и короткими экспирациями; вопрос «кто платит за лаг»; вклад.
2. Institutional background: продукт, оракул, CLOB, хронология режимов (таблица выше).
3. Theory: стейл-котировка бинарного контракта, «гамма»-потери ~ лаг/√τ, no-trade band от fee(p), предсказания для speed bump и TWAP.
4. Data: источники, синхронизация часов, валидация ончейн/фид.
5. Measuring latency: lead–lag (HY/HRY), event study, гонки.
6. Who wins: классификация адресов, декомпозиция ренты (снайпер / мейкер / комиссия / ребейт).
7. Design changes as natural experiments: комиссии (01/03.2026), форма кривой (30.03), TWAP (07.08), speed bump (17.08, 04.09); DiD против 1H/Kalshi.
8. Welfare and policy: сравнение инструментов; связь с темами 04/05.
9. Conclusion; приложение: устойчивость, этика данных (анонимизация).

---

## Источники

**Polymarket (первичные)**
- Fees: https://docs.polymarket.com/trading/fees
- Maker Rebates: https://docs.polymarket.com/programs/maker-rebates ; https://docs.polymarket.com/polymarket-learn/trading/maker-rebates-program
- Changelog: https://docs.polymarket.com/changelog/changelog
- Order lifecycle (taker delay): https://docs.polymarket.com/concepts/order-lifecycle
- V2 migration: https://docs.polymarket.com/v2-migration
- Contracts: https://docs.polymarket.com/resources/contracts ; Blockchain data: https://docs.polymarket.com/resources/blockchain-data
- X @PolymarketDevs о taker delay (05.06.2026): https://x.com/PolymarketDevs/status/2061930696323830158
- API (проверено 26.10.2026): https://gamma-api.polymarket.com/events?slug=btc-updown-15m-1793023200 ; https://data-api.polymarket.com/trades ; https://clob.polymarket.com/prices-history
- Chainlink TWAP stream: https://data.chain.link/streams/btc-usd-twap-60s-streams

**Пресса и аналитика**
- The Block, 06.01.2026: https://www.theblock.co/post/384461/polymarket-adds-taker-fees-to-15-minute-crypto-markets-to-fund-liquidity-rebates
- Cointelegraph, 06.01.2026: https://cointelegraph.com/news/polymarket-quietly-adds-taker-fees-15-minute-crypto-markets
- DeFi Rate: https://defirate.com/news/polymarket-users-approve-new-crypto-market-fees/
- Finance Magnates, 07.01.2026: https://www.financemagnates.com/cryptocurrency/polymarket-introduces-dynamic-fees-to-curb-latency-arbitrage-in-short-term-crypto-markets/
- Pine Analytics, Fee Rollout: https://pineanalytics.substack.com/p/polymarket-fee-rollout
- Blockworks Research, Fee switch: https://blockworks-research.beehiiv.com/p/polymarket-s-fee-switch
- PYMNTS (5m boom): https://pymnts.com/cryptocurrency/2026/polymarket-enjoys-boom-in-five-minute-crypto-bets
- Dune blog, fast markets (сейчас 404): https://dune.com/blog/polymarket-fast-markets
- Telonex, top 15m traders: https://telonex.io/research/top-crypto-traders-polymarket-15m
- BeInCrypto (боты): https://beincrypto.com/arbitrage-bots-polymarket-humans/
- Coinpaprika (TWAP после манипуляций): https://coinpaprika.com/news/polymarket-rewrites-bitcoin-settlement/
- Kalshi market rules: https://help.kalshi.com/en/articles/13823838-market-rules

**Практики (низкая уверенность)**
- https://github.com/Yak0vkaSup/polymarket-microstructure
- https://www.indiehackers.com/post/latency-arbitrage-in-15-minute-crypto-markets-building-a-polymarket-trading-edge-2026-f77cc226c0
- https://dev.to/lkto1m/why-my-polymarket-bot-watches-chainlink-not-binance-the-oracle-gap-that-changes-every-close-1e96
- https://benjamincup.medium.com/unlocking-edges-in-polymarkets-5-minute-crypto-markets-last-second-dynamics-bot-strategies-and-db8efcb5c196
- https://www.quantvps.com/blog/binance-to-polymarket-arbitrage-strategies
- https://polybot.trading/blog/polymarket-taker-delay-250ms-to-50ms

**Академические**
- Dai, Jia, Yu (2026), Settlement Manipulation in Prediction Markets: https://arxiv.org/abs/2606.31675
- Young (2026), OpenMarket: https://arxiv.org/abs/2607.26245
- Dubach (2026), Anatomy of a Decentralized Prediction Market: https://arxiv.org/abs/2604.24366 ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6658364
- Saguillo et al. (2025), Unravelling the Probabilistic Forest: https://arxiv.org/abs/2508.03474
- Gebele, Mutzel, Matthes (2026), Executable Arbitrage: https://arxiv.org/abs/2608.00666
- Arbitrage in Polymarket NBA markets (2026): https://arxiv.org/abs/2605.00864
- Lejmi (2026), MARL market making: https://arxiv.org/abs/2610.26789
- Moallemi, Robinson, Zhu (2026), Uniform-Loss AMM for Prediction Markets: https://arxiv.org/abs/2607.17428
- Milionis, Moallemi, Roughgarden, Zhang (2022), LVR: https://arxiv.org/abs/2208.06046
- Milionis, Moallemi, Roughgarden (2023), Arbitrage profits with fees: https://arxiv.org/abs/2305.14604
- Bürgi, Deng, Whelan, Makers and Takers (Kalshi): https://www.karlwhelan.com/Papers/Kalshi.pdf ; https://cepr.org/publications/dp20631
- Budish, Cramton, Shim (2015), QJE 130(4): https://doi.org/10.1093/qje/qjv027
- Aquilina, Budish, O'Neill (2022), QJE 137(1): https://doi.org/10.1093/qje/qjab032
- Foucault, Kozhan, Tham (2017), Toxic Arbitrage, RFS 30(4)
- Menkveld, Zoican (2017), RFS 30(4); Baldauf, Mollner (2020), JF 75(3); Shkilko, Sokolov (2020), JF 75(6); Brolley, Cimon (2020), JFQA 55(8)
- Wolfers, Zitzewitz (2004), Prediction Markets, JEP 18(2)
- Hayashi, Yoshida (2005), Bernoulli 11(2); Hoffmann, Rosenbaum, Yoshida (2013), Bernoulli 19(2); Huth, Abergel (2014), J. Empirical Finance 26; Hasbrouck (1995), JF 50(4)

*Выходные данные классических статей (тома и номера) приведены по памяти. Перед подачей сверить.*
