# RESEARCH: Учитывают ли рынки предсказаний риск ликвидаций? Барьерные контракты Polymarket и on-chain плечо

*Do Prediction Markets Price Liquidation Risk? On-Chain Leverage and Barrier Contracts on Polymarket*

Дата ресерча: 2026-10-26. Метки уверенности: **[проверено]** — сам посмотрел первоисточник или API; **[вторично]** — по аннотации, пересказу или стороннему агрегатору; **[не подтверждено]** — встречается в одном источнике или нашёл только косвенно.

---

## 0. Коротко

1. Критика «цену берут из агрегатора» к барьерным рынкам **фактически неверна**. Рынки «What price will Bitcoin/Ethereum hit…» разрешаются по **одной площадке**: Binance BTC/USDT (ETH/USDT) спот, High/Low 1-минутной свечи. Агрегатор (Chainlink Data Streams) используется в других рынках — «Up or Down» на 5/15 минут. **[проверено, Gamma API]**
2. Верная часть критики в другом: Polymarket не видит позиций. Ликвидации на Hyperliquid срабатывают по оракулу и медиане бирж, на Aave — по Chainlink, то есть не по свече Binance-спот. Влияние на исход контракта возможно только через цену: каскад, затем проскок спота на Binance.
3. Канал виден на конкретном событии. 10.10.2025 BTC/USDT на Binance-спот в 21:20 и 21:24 UTC упал до **ровно 102 000.00**. Ниже 105k цена была всего ~4 минуты. Барьерные рынки «dip to $104k/106k…114k in October» и недельные «dip to $110k–118k Oct 6–12» разрешились «Да» по этой тени свечи. Минимумы в тот день разные по площадкам: Binance-перп 101 516.5, Hyperliquid 100 837. **[проверено, API Binance/Hyperliquid/Gamma]**
4. Главная угроза новизне: путь-зависимые рынки Polymarket уже сравнивали с опционами. Fabi–Marfè–Ruffo–Schönleber: «Reach/Dip» заметно отклоняются от бенчмарка по опционам, рынки «Above/Range» — нет. Магистерская Olsen (AAU, 2026): 258 месячных барьеров BTC, модель касания объясняет >95% вариации, цены ближе к оценке по реализованной волатильности, чем по implied. Связь с **ликвидациями/плечом** в найденной литературе не исследована. **[вторично]**
5. Вердикт: тема выживает в переформулировке **«level-specific jump risk»**, то есть риск скачка, привязанный к уровню цены. Реализуемость 3/5, новизна 3/5. Брать стоит, если сначала доказать, что сам физический канал существует (этап 1 ниже).

---

## 1. Механика барьерных рынков Polymarket

### 1.1 Семейства рынков (BTC, ETH; по Gamma API `public-search`) **[проверено]**

| Семейство | Пример slug | Типичный объём |
|---|---|---|
| Годовой | `what-price-will-bitcoin-hit-in-2025` | $189 млн (2025); `…-before-2027` — $78 млн на 26.10.2026 |
| Месячный | `what-price-will-bitcoin-hit-in-october-2026` | $20–120 млн (янв. 2026 — $108 млн, фев. 2026 — $121 млн, окт. 2025 — $43.6 млн) |
| Недельный | `what-price-will-bitcoin-hit-october-6-12` | $2–6 млн |
| Дневной | `what-price-will-bitcoin-hit-on-october-25-2026` | $0.1–0.4 млн, страйки шагом $1k |
| «by date» | `what-price-will-bitcoin-hit-by-march-31` | $50 млн |

Каждое событие — это лестница бинарных рынков «Will Bitcoin reach $X» (вверх) и «Will Bitcoin dip to $X» (вниз). Пример: в месячном рынке на октябрь 2026 — 19 активных страйков от $60k до $150k с шагом $2.5k. Общий объём $11.6 млн, заявленная ликвидность $1.53 млн, на отдельный страйк ~$50–110k ликвидности. Для ETH есть такие же рынки: октябрь 2026 — $2.9 млн объёма.

### 1.2 Правило разрешения (дословно из Gamma API, рынок «Will Bitcoin reach $90,000 in October?») **[проверено]**

> This market will immediately resolve to "Yes" if any Binance 1 minute candle for BTC/USDT during the month specified in the title (from 00:00 AM ET on the first day to 11:59 PM ET on the last), has a final High price equal to or greater than the price specified in the title… The resolution source… is Binance, specifically the BTC/USDT High prices… with the chart settings on "1m"… Prices from other exchanges, different trading pairs, or spot markets will not be considered.

Что из этого следует:
- **Мониторинг фактически непрерывный.** High/Low минутной свечи фиксирует любой принт внутри минуты, включая однотиковую тень. Поправка на дискретный мониторинг (Broadie–Glasserman–Kou) почти не нужна.
- **Одна площадка — спот Binance**, без индекса и без перпа. Значит, важна тень свечи именно на этой площадке, а не на «рынке в целом».
- Рынок разрешается **сразу после касания**, а не в экспирацию. Это классический one-touch с выплатой при касании.
- Окна задаются в ET (00:00–23:59 ET), а не в UTC. Это нужно учесть при сопоставлении с Deribit (экспирация 08:00 UTC).
- Рынки «Bitcoin Up or Down» (5/15 мин, часовые) разрешаются по **Chainlink Data Streams BTC/USD** — это агрегатор. Похоже, критика из README путает эти семейства. **[вторично — polyguana, Bitcoin Magazine]**

### 1.3 Особенности данных
- В одном событии встречаются **повторы рынков с одинаковым вопросом**: разные `conditionId`, разные `closedTime`, иногда противоположный исход. Пример: «Will Bitcoin reach $100,000 by December 31, 2025?» встречается дважды, Yes 06.01.2025 и No. Скорее всего, страйки перевыставляли или меняли полярность. **Причина не выяснена.** Очищать нужно по `conditionId`/`clobTokenIds` и дате создания. **[проверено, что повторы есть; причина — не подтверждено]**
- `closedTime` — это время записи разрешения, а не время касания. Момент касания берём из 1m-свечей Binance.

---

## 2. Разбор критики: есть ли канал «ликвидации → касание»

### 2.1 Где критика права
- Polymarket ничего не знает о позициях, механической связи нет.
- Триггеры ликвидаций срабатывают **не по свече Binance-спот**. Hyperliquid ликвидирует по mark price: это смесь оракула (взвешенная медиана CEX-спота) и стакана HL. **[вторично — документация HL]** Aave/Compound ликвидируют по Chainlink. Поэтому кластер ликвидаций «на уровне X» в разных системах срабатывает при разных ценах Binance-спота.
- По перповым CEX (Binance, Bybit, OKX) **позиции не публичны**. «Карты ликвидаций» Coinglass — это **модельные оценки** по OI и типичным плечам, а не наблюдаемые данные. Значит, для основного объёма плеча регрессор измеряется с ошибкой. **[вторично — описания вендоров]**

### 2.2 Где канал всё же есть
- **Позитивная обратная связь.** Ликвидация — это принудительный рыночный ордер по тренду. Классический аналог — стоп-лоссы на валютном рынке у Osler (NY Fed SR 125/150). Стопы кластеризуются у круглых уровней, а при достижении кластера тренд ускоряется («price cascades»). Это даёт тяжёлые хвосты. Take-profit, наоборот, дают отскоки. **[вторично]**
- **DeFi.** Lehar–Parlour (BIS WP 1062): продажи залога при ликвидациях на Aave/Compound дают временный и постоянный ценовой импакт на DEX. В волны ликвидаций эти продажи объясняют заметную часть доходности залогового токена. Perez et al.: на Compound изменение цены на 3% делало ликвидируемыми >$10 млн. **[вторично]**
- **Событие 10–11.10.2025.** По данным Coinglass ликвидировано >$19 млрд (CoinShares считает, что реально больше). OI фьючерсов упал примерно с $175 до $125 млрд. Hyperliquid перед событием держал около трети OI (Laevitas, через The Defiant). Маркет-мейкеры сняли ликвидность, на HL сработал ADL. **[вторично]**
  - Мои замеры по API **[проверено]**:
    - BTC/USDT спот Binance: дневной High 122 550, Low **102 000.00**, Close 112 774.
    - BTCUSDT перп Binance: Low 101 516.5.
    - Hyperliquid BTC: Low 100 837.
    - ETH/USDT спот: Low 3 435, Close 3 830.
    - 1m-свечи спота: 21:19 — Low 103 800; 21:20 — Low 102 000, Close 104 385; 21:24 — снова Low 102 000, Close 108 219. Свечей с Low < 105k — 4, с Close < 105k — 2.
  - То есть касание «dip $104k» случилось за **1–2 минуты** тени. Цена закрытия дня была на ~10% выше барьера. Для one-touch важен именно такой проскок, и лог-нормальная модель на дневной волатильности его не даёт.
  - Минимум **ровно на 102 000.00, дважды** похож на крупную лимитную стену или кластер стопов у круглого уровня — сюжет Osler в крипте.
  - Разброс минимумов между площадками ~1.2%. Значит, у барьерного контракта на одной площадке есть **идиосинкратический риск тени**, который индексы и опционы не видят.
- **Эмпирика каскадов на перпах (препринты 2026, без рецензирования) [вторично]**:
  - Garcia Seuma, arXiv 2607.27070: 7 каскадов на Binance-перпе, 2022–2025. Ни один индикатор раннего предупреждения не работает для всех событий.
  - Он же, arXiv 2608.03616: по on-chain логу исполнений коэффициент ветвления каскада 10.2025 ≈ 0.1–0.2, то есть субкритический. Основная масса принудительных продаж прошла за ~30 минут, значительную часть поглотил бэкстоп площадки. Тяжесть определяли размер шока, структура рынка и уход ликвидности, а не «мультипликатор».
  - Sepper, arXiv 2603.09164: «Slippage-at-Risk» по стакану Hyperliquid.
  - Lim Boon Chuan (JFDA): глубина стакана HL через 23 дня после события держалась на уровне 66–79% от исходной.

  Вывод для темы: **сами каскады умеренные, но разрушается ликвидность**. Короткая глубокая тень — ровно то, что включает one-touch.
- **«Магнитный эффект» уровней ликвидаций.** Рецензируемой эмпирики не нашёл, есть только вендорские утверждения (Coinglass, CMC, TradingView). **[не подтверждено]** Это пробел, который можно закрыть в статье.

### 2.3 Альтернативный канал: манипуляция
Dai–Jia–Yu, «Settlement Manipulation in Prediction Markets» (arXiv 2606.31675, Stanford/SMU) — **[вторично]**:
- На 5-минутных рынках «Up/Down» трейдеры толкают спот на Binance в последние секунды. Около 821 кошелька заработали $8.2 млн.
- Для барьеров на одной площадке и при непрерывном мониторинге стимул «дотолкнуть до уровня» ещё сильнее.
- Касания из-за тени свечи надо отделять от касаний, где тень вызвал кто-то с позицией на Polymarket. Это и конкурирующее объяснение, и отдельный результат.

### 2.4 Выживает ли тема
**Да, но не как «Polymarket учитывает ликвидации».** Рабочая формулировка:

> *Риск касания зависит от уровня. Кластеры плечевых позиций (наблюдаемые on-chain на Hyperliquid/Aave) и круглые уровни повышают условную вероятность проскока через барьер сверх того, что даёт гладкая модель (GBM, гладкая улыбка Deribit). Вопрос: закладывает ли это лестница барьерных цен Polymarket?*

Сильная сторона формулировки: гладкая поверхность опционов в принципе **не может** отразить «комковатость» риска по уровням, а лестница страйков Polymarket с шагом $1–2.5k может. Так у рынка предсказаний появляется информационная роль, которую Olsen для барьеров в целом не нашёл.

---

## 3. Литература

**Ликвидации в DeFi**
- Qin, Zhou, Gamito, Jovanovic, Gervais (2021). *An Empirical Study of DeFi Liquidations: Incentives, Risks, and Instabilities*. ACM IMC '21, arXiv 2106.06389. Aave/Compound/Maker/dYdX; механизмы продают избыточный дисконтированный залог. **[проверено — аннотация]**
- Perez, Werner, Xu, Livshits (2021). *Liquidations: DeFi on a Knife-edge*. FC 2021, arXiv 2009.13235. **[проверено — аннотация]**
- Lehar, Parlour (2022). *Systemic Fragility in Decentralized Markets*. BIS WP 1062. Ценовой импакт ликвидационных продаж и заражение через оракулы. **[вторично]**
- Дополнительно, не проверял: Chiu, Ozdenoren, Yuan, Zhang — *On the Fragility of DeFi Lending* (теория долговых спиралей в DeFi). **[не подтверждено — точные выходные данные]**

**Каскады, плечо, перпы**
- Garcia Seuma (2026): arXiv 2607.27070 и 2608.03616 (выше). **[вторично]**
- Sepper (2026), arXiv 2603.09164; Lim Boon Chuan, J. FinTech & Digital Assets (ликвидность HL после 10.10). **[вторично]**
- Liquidation, Leverage and Optimal Margin in Bitcoin Futures Markets: EVT по BitMEX, arXiv 2102.04591. **[вторично]**
- Классика: Brunnermeier–Pedersen (2009, RFS), liquidity spirals; Gennotte–Leland (1990, AER), крах от хеджирования; Osler (2003 JF; 2005 JIMF / NY Fed SR 150), стоп-лосс каскады. **[по памяти, выходные данные проверить]**
- Gornall, Rinaldi, Xiao — перпы и базисный риск (AEA 2026). **[вторично]**

**Ценообразование one-touch / барьеров**
- Reiner–Rubinstein (1991), *Breaking down the barriers*, Risk; Rubinstein–Reiner — бинарные и барьерные опционы в замкнутой форме. **[по памяти]**
- Broadie–Glasserman–Kou (1997, Math. Finance) — поправка на дискретный мониторинг. Kou–Wang (2003, Adv. Appl. Prob.) — время первого прохождения для double-exponential jump-diffusion, то есть аналитика касания со скачками. **[по памяти]**
- Практика FX: one-touch котируют с поправкой vanna-volga (Wystup; Castagna–Mercurio). Это аналог «рыночного» бенчмарка поверх улыбки. **[по памяти]**

**Рынки предсказаний против опционов (прямые конкуренты)**
- Fabi, Marfè, Ruffo, Schönleber (2026). *Are Decentralized Prediction Markets Efficient? Evidence from Bitcoin Options* / *Market Efficiency in Prediction Markets — A Comparison with Derivatives*, SSRN 6565258, FC'26 DeFi workshop. Рынки «Reach/Dip» отклоняются от бенчмарка по опционам сильнее, чем «Above/Range». Ошибки больше на старте и у экспирации, на выходных и в периоды макронеопределённости. **[вторично — аннотация; PDF не распарсил]**
- Akey et al. (2026). *Who Wins and Who Loses in Prediction Markets? Evidence from Polymarket*, SSRN 6443103. Отклонения максимальны в хвостах и при высокой волатильности. **[вторично; у агрегатора аннотация совпадает с Fabi et al. — проверить]**
- Olsen (2026). *The informational content of prediction markets: evidence from Polymarket Bitcoin contracts*, магистерская AAU. 258 месячных барьеров BTC (10.2024–03.2026) + 252 ETH. Калибровка не отвергается. Модель касания объясняет >95%. Цены ниже бенчмарка по implied vol, но совпадают с бенчмарком по реализованной (это VRP). Granger-предсказательной силы нет. **[вторично]**
- Portnaya (2026). *Do Prediction Markets Match Option Prices?*, arXiv 2606.19517. Пороговые (не барьерные) контракты против опционов Binance; разрыв ~5.6 п.п. **[вторично]**
- BSIC: Kalshi «above» против Deribit (SVI + Breeden–Litzenberger); one-touch исключены. **[вторично]**
- Dai, Jia, Yu (2026), манипуляция расчётом (выше).
- Классика эффективности: Wolfers–Zitzewitz (2004, JEP); Snowberg–Wolfers (2010, JPE), favorite-longshot bias; Manski (2006). Про VRP в крипте: Alexander–Imeraj (Bitcoin VIX / variance risk premium). **[по памяти]**

---

## 4. Данные

| Источник | Что даёт | Доступ | Уверенность |
|---|---|---|---|
| Polymarket Gamma API (`gamma-api.polymarket.com/events?slug=…`, `/public-search`) | метаданные, правила, страйки, объём, `clobTokenIds`, closedTime | бесплатно, без ключа | **[проверено]** |
| Polymarket CLOB `GET /prices-history` | история цены токена; `interval` ∈ {1m,1h,6h,1d,1w,max,all}, `fidelity` в минутах (по умолчанию 1), `startTs/endTs`; есть batch-версия | бесплатно; хранение истории для старых рынков не документировано — проверить на рынках 2024–2025 | **[проверено — док.]** |
| Сделки Polymarket (Polygon, CTF Exchange `OrderFilled`) | тиковые сделки, кошельки (для анализа манипуляций) | Dune (таблицы polymarket_polygon.*), Goldsky subgraph | **[вторично]** |
| Binance 1m klines (`data-api.binance.vision`, data.binance.vision дампы) | ровно источник разрешения; также перп (fapi) | бесплатно | **[проверено]** |
| Hyperliquid info API (`clearinghouseState` по адресу → `liquidationPx`, размер, плечо) | наблюдаемые уровни ликвидаций | бесплатно, но только **текущее** состояние по адресу; общего списка адресов нет | **[вторично — документация, сторонние гайды]** |
| Hyperliquid S3 (`hl-mainnet-node-data`: `node_trades` → `node_fills` → `node_fills_by_block`; `hyperliquid-archive`: L2-снапшоты, asset ctxs) | исторические исполнения со всеми адресами → реконструкция позиций | requester-pays; по Dwellir, fills примерно с марта 2025 | **[вторично]** |
| Сторонние снапшоты HL (CoinMarketCap HL heatmap «каждые ~5 мин», Hyperdash, Hydromancer) | готовая история позиций/карт | частично платно, условия не проверял | **[не подтверждено]** |
| Coinglass API (heatmap model1/model2, liquidation map, история 12h–1y) | **модельная** карта ликвидаций CEX | $29–699/мес; heatmap, по стороннему README, только на Professional ($699) | цены **[проверено]**, тариф heatmap **[не подтверждено]** |
| Aave v3 (события Borrow/Supply/LiquidationCall; subgraph; Dune `aave_v3_*`) | health factor и цена ликвидации по ETH/WBTC-залогу во времени | бесплатно (Dune/subgraph), реконструкция трудоёмкая | **[вторично]** |
| Deribit опционы | IV-поверхность — бенчмарк Q | Tardis.dev: `options_chain` с 2019-03-30, первые числа месяца бесплатно; полный доступ платный (академические скидки есть, не проверял). Альтернативы: Amberdata, Coin Metrics, Deribit public API для текущего | **[вторично]** |

Объём выборки. По месячным BTC: ~24 события × ~20 страйков, плюс ETH. По недельным: около 100 событий × ~14 страйков. Дневные рынки дают тысячи страйк-дней, **но с какого момента они существуют, не выяснял**. Страйки внутри события сильно коррелированы, независимых «эпизодов приближения к уровню» гораздо меньше.

---

## 5. Методология

### 5.1 Модельная вероятность касания (бенчмарки)
1. **GBM, аналитика.** Для барьера вверх H > S, μ = r − σ²/2:
   P = N((ln(S/H)+μT)/(σ√T)) + (H/S)^{2μ/σ²} · N((ln(S/H)−μT)/(σ√T)).
   При μ≈0 это ≈ 2·N(−|ln(H/S)|/(σ√T)) — принцип отражения. Варианты σ:
   - (a) ATM IV Deribit на сроке, интерполированном к ET-окну;
   - (b) IV на страйке барьера;
   - (c) реализованная волатильность (мера P; по Olsen рынок ближе к ней).
2. **Согласованный с улыбкой бенчмарк Q.** Калибровать Bates (SVJ) или Kou к поверхности Deribit на дату, затем вероятность касания Монте-Карло. Дешёвая альтернатива — vanna-volga поправка к цене по GBM.
3. **Физический бенчмарк P без модели.** Блочный бутстрап 1m-траекторий Binance-спот (или Kou/Hawkes с самовозбуждением, оценённые по истории). Даёт вероятность касания с учётом реальных теней свечей.
4. Мониторинг непрерывный (High/Low 1m), поправка BGK не нужна. Окна в ET, касание засчитывается с первого принта.

### 5.2 Этап 1 — существует ли канал физически (Polymarket не нужен)
- Единица наблюдения: эпизод, когда цена приблизилась к уровню L на расстояние d (например, 0.5–1%).
- Зависимая переменная: вероятность и глубина проскока через L в течение τ минут.
- Регрессоры:
  - **плотность ликвидаций** около L — notional позиций HL с `liquidationPx` в [L−δ, L], плюс Aave по ETH/WBTC;
  - круглость уровня;
  - контроли: OI, funding, реализованная волатильность, глубина стакана Binance, время суток и выходные.
- Метод: hazard-модель первого прохождения или логит, плюс event study вокруг кластеров (в духе Osler).
- Если эффекта нет, этап 2 теряет смысл.

### 5.3 Этап 2 — учитывает ли Polymarket
`mispricing_{i,t} = p^PM_{i,t} − p^model_{i,t}` для страйка i в момент t (часовые или 10-минутные снапшоты),
`mispricing = α + β·LiqDensity(H_i, t) + γ·X + FE(event) + ε`.

- Контроли X: |ln(H/S)|/(σ√T), время до экспирации, спред и глубина книги Polymarket, объём, выходные, макрособытия, VRP (IV − RV), круглость H, направление (reach против dip).
- Ожидаемый знак: если рынок учитывает плечо, β > 0 для «dip»-страйков под крупными лонг-кластерами (и для «reach» над шорт-кластерами), сверх бенчмарка P. Ключевая версия — сравнить с бенчмарком **P с тенями свечей**: учитывает ли рынок уровень сверх того, что даёт безусловное распределение теней.
- Проверка «знания vs исход»: Brier-разложение и скоринг. Улучшает ли добавление LiqDensity к модельной вероятности прогноз касания вне выборки? Если да, а цена Polymarket это не отражает, у рынка неэффективность.
- Устойчивость:
  - ETH отдельно (у ETH сильнее DeFi-плечо: Aave, ликвидационные уровни ETH);
  - исключить 10.10.2025;
  - взять только Hyperliquid, где позиции наблюдаемы, или Coinglass как зашумлённую замену для CEX — тогда нужна поправка на ошибку измерения в регрессоре (инструмент: HL-плотность для Coinglass-плотности);
  - перекрёстная проверка по площадкам: тень Binance-спот против HL/Binance-перп.
- Эндогенность: плечо копится там, где ждут движения. Идеи инструментов — изменения параметров риска Aave (LT/LTV по голосованиям governance), механические сдвиги уровней ликвидации из-за накопленного funding.

---

## 6. Новизна, риски, вердикт

**Новизна (3/5).** Неточность цен путь-зависимых рынков Polymarket против опционов уже показали Fabi et al. и Olsen. Новое здесь: (i) **риск, зависящий от уровня**, и наблюдаемое on-chain плечо как его источник; (ii) риск тени на одной площадке (правило разрешения по Binance-спот) и разрыв минимумов между площадками; (iii) «барьерная лестница» как инструмент, которого нет у гладкой улыбки. Эмпирики «магнитов ликвидаций» в рецензируемой литературе не нашёл, это отдельный вклад.

**Реализуемость (3/5).**
- Polymarket и Binance — бесплатно и просто.
- Deribit IV — Tardis, платно или первые числа месяца.
- Главная трудность — **историческая** карта ликвидаций Hyperliquid: реконструкция из `node_fills` (S3, requester-pays) с марта 2025, либо сторонние снапшоты.
- Aave — реконструкция по событиям, трудоёмко, но решаемо.
- По CEX — только модельные оценки Coinglass.

**Ключевые риски.**
1. **Мощность теста.** Мало независимых эпизодов, каскады редки. Один день 10.10.2025 может определять весь результат.
2. HL — лишь часть плеча. После 10.2025 его доля в OI могла сильно измениться. **[не подтверждено]**
3. Эндогенность плотности ликвидаций.
4. Тонкие книги Polymarket на дальних страйках: цены 0.1–1¢ не информативны.
5. Конкурирующие объяснения: манипуляция расчётом (Dai et al.), VRP, favorite-longshot.
6. Особенности данных Gamma (повторы рынков).

**Вердикт: брать — с переформулировкой и в два этапа.** Исходная формулировка («Polymarket учитывает ликвидации?») против критики не устоит: механической связи нет, а CEX-позиции не наблюдаемы. Устойчивая формулировка:

> **«Wicks, Leverage and First Passage: Level-Specific Jump Risk in Prediction-Market Touch Contracts»** (или *Do Prediction Markets Price Level-Specific Crash Risk? Evidence from Leverage Clusters and Polymarket Barrier Ladders*).
> Этап 1: on-chain кластеры плеча (Hyperliquid, Aave) и круглые уровни повышают вероятность проскока через барьер на Binance-спот сверх гладких моделей.
> Этап 2: закладывают ли это цены барьерной лестницы Polymarket — относительно Deribit-Q и физического бенчмарка с тенями свечей. Отдельный раздел — риск тени на одной площадке и манипуляция.

Если этап 1 даст ноль, остаётся честная, но менее яркая статья: «барьерные рынки Polymarket против моделей с тенями свечей и скачками». Это продолжение Fabi et al./Olsen с упором на правило разрешения по одной площадке и на событие 10.10.2025.

---

## Источники

Polymarket / правила / данные
- Gamma API, событие октябрь 2026: https://gamma-api.polymarket.com/events?slug=what-price-will-bitcoin-hit-in-october-2026
- Страница рынка: https://polymarket.com/event/what-price-will-bitcoin-hit-in-october-2026
- Gamma API, октябрь 2025: https://gamma-api.polymarket.com/events?slug=what-price-will-bitcoin-hit-in-october-985
- Gamma API, неделя 6–12.10.2025: https://gamma-api.polymarket.com/events?slug=what-price-will-bitcoin-hit-october-6-12
- CLOB prices-history: https://docs.polymarket.com/api-reference/markets/get-prices-history.md
- Batch prices-history: https://docs.polymarket.com/api-reference/markets/get-batch-prices-history.md
- Зеркало правил Up/Down (Chainlink): https://polyguana.com/market/2347657
- Binance klines (источник разрешения): https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1m

Событие 10.10.2025 и каскады
- The Defiant, «The Ultimate 10/10 Crash Autopsy»: https://thedefiant.io/newsletter/defi-daily/the-ultimate-10-10-crash-autopsy
- CoinShares, «Billions in liquidations: what happened?»: https://coinshares.com/insights/knowledge/billions-in-liquidations-what-happened/
- Amberdata, «How $3.21B vanished in 60 seconds»: https://blog.amberdata.io/how-3.21b-vanished-in-60-seconds-october-2025-crypto-crash-explained-through-7-charts
- Garcia Seuma, arXiv 2607.27070: https://arxiv.org/pdf/2607.27070
- Garcia Seuma, arXiv 2608.03616: https://arxiv.org/abs/2608.03616
- Sepper, arXiv 2603.09164: https://arxiv.org/html/2603.09164v1
- Lim Boon Chuan, JFDA: https://journals.lincoln.ac.nz/index.php/JFDA/article/view/1395
- Bitcoin futures liquidation/EVT, arXiv 2102.04591: https://arxiv.org/abs/2102.04591v1
- Osler, NY Fed SR 150: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
- Osler, NY Fed SR 125: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf

DeFi-ликвидации
- Qin et al., arXiv 2106.06389: https://arxiv.org/abs/2106.06389v2
- Perez et al., arXiv 2009.13235: https://arxiv.org/pdf/2009.13235
- Lehar–Parlour, BIS WP 1062: https://www.bis.org/publ/work1062.pdf
- Aave governance, ETH price shock simulation: https://governance.aave.com/t/independent-liquidation-risk-analysis-aave-v3-ethereum-mainnet-eth-price-shock-simulation/24408
- Aave liquidations docs: https://docs.aave.com/developers/guides/liquidations

Рынки предсказаний против опционов
- Fabi, Marfè, Ruffo, Schönleber (FC'26): https://fc26.ifca.ai/defi/papers/market-efficiency-prediction-markets.pdf ; SSRN 6565258: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6565258
- Akey et al., SSRN 6443103: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6443103
- Обзор (Capital Spectator, 24.04.2026): https://www.capitalspectator.com/?p=25500
- Olsen, AAU: https://projekter.aau.dk/the-informational-content-of-prediction-markets-evidence-from-polymarket-bitcoin-contracts-628468cf.html
- Portnaya, arXiv 2606.19517: https://arxiv.org/pdf/2606.19517
- BSIC, Kalshi vs Deribit: https://bsic.it/well-can-they-predict-an-investigation-of-crypto-prediction-contracts/
- Dai–Jia–Yu, Settlement Manipulation (через Bitcoin Magazine): https://bitcoinmagazine.com/news/traders-took-8-2-million-from-polymarkets ; arXiv 2606.31675 (номер не проверен): https://arxiv.org/pdf/2606.31675
- Polymarket oracle adjudication, arXiv 2609.15368: https://arxiv.org/pdf/2609.15368

Данные о плече и опционах
- Hyperliquid liquidations: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/liquidations
- Hyperliquid historical data: https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data
- Dwellir, архив HL: https://www.dwellir.com/docs/hyperliquid/archival-data
- Goldrush, HL liquidation monitor: https://goldrush.dev/guides/building-a-real-time-hyperliquid-liquidation-monitor-part-1/
- Coinglass pricing: https://coinglass.com/pricing ; heatmap API: https://docs.coinglass.com/reference/liquidation-heatmap
- CoinMarketCap liquidation heatmap: https://coinmarketcap.com/charts/liquidation-heatmap/
- Tardis.dev Deribit: https://docs.tardis.dev/historical-data-details/deribit.md
- Coin Metrics implied vol: https://docs.coinmetrics.io/market-data/market-data-overview/volatility/implied-volatility
