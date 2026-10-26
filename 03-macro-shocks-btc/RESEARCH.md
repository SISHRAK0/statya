# RESEARCH: Prediction Market Shocks as Trading Signals — Do Polymarket Macro Odds Lead Bitcoin?

*Ресерч на 2026-10-26. Пометки уверенности: **[подтв.]** — первоисточник или несколько независимых источников; **[вероятно]** — один вторичный источник или аннотация; **[не подтв.]** — моё предположение / не нашёл подтверждения.*

## TL;DR

- Прямой работы «шоки вероятностей Polymarket по макро/политике → BTC на внутридневной частоте» я не нашёл. Есть соседние: price discovery внутри prediction markets (Polymarket против Kalshi, Polymarket против Betfair), latency Polymarket против Binance на собственных BTC-рынках Polymarket, качество прогнозов Kalshi по макро (ФРС), Trump-посты против fed funds futures. Ниша свободна.
- Ключевая идентификационная проблема подтверждается фактурой: крупные шоки (тарифы 09.04.2025, 10.10.2025, выбор Warsh в январе 2026) приходят **через пост Trump в Truth Social**, на который BTC реагирует за секунды–минуты. «Опережение» Polymarket в таких эпизодах почти наверняка общий фактор. Исключения, где Polymarket правда может быть впереди: утечки и insider-ставки (Maduro, январь 2026; перемирие с Ираном, апрель 2026) и медленное накопление информации (номинации, шатдауны, суды).
- Рекомендованная подача: не «торговая стратегия», а **price discovery / information share между рынком событий и рынком актива** плюс event study с вероятностями как мерой сюрприза (в линии Snowberg–Wolfers–Zitzewitz). Реализуемость 4/5, новизна 3.5/5.

---

## 1. Релевантные рынки Polymarket и Kalshi и их ликвидность

**Категории, которые имеют смысл для BTC** (по убыванию ожидаемой силы связи):

1. **Решения FOMC** (Polymarket «Fed decision in <month>», Kalshi `KXFEDDECISION`). Самые ликвидные макро-рынки. Сентябрь 2025 на Polymarket — более $220M объёма, «largest FOMC market ever» **[вероятно]**, по одной французской статье. По агрегатору polyguana: октябрь 2025 — ~$102M, январь 2026 — ~$107M **[вероятно]**. На Kalshi Fed-контракты в 2026 году, по агрегаторам, самые торгуемые не-спортивные рынки **[вероятно]**. Но спорт даёт ~85% объёма Kalshi (апрель 2026, $3.04B из $3.54B за неделю) **[вероятно]**.
2. **Назначение председателя ФРС.** Чистый эксперимент января 2026: в день перед объявлением вероятность Kevin Warsh выросла с ~39% до ~93–95%, Kalshi показал то же. BTC в том же окне упал к ~$81k, рынок читал Warsh как «ястреба» **[вероятно]**, The Block и др. Объявление вышло постом в Truth Social **[подтв.]**.
3. **CPI / инфляция** (Kalshi — лестница порогов CPI, core CPI). Есть свежая работа Angelini (arXiv 2606.30040): из соседних пороговых контрактов строится распределение инфляции, и хвостовые вероятности несут информацию сверх консенсуса Reuters **[подтв.]**, по аннотации. Для BTC это даёт меру «инфляционного сюрприза» до релиза.
4. **Тарифы и торговая политика**: «тарифы против страны X к дате», «пауза», дело в Верховном суде о тарифах по IEEPA. Ликвидность у этих рынков низкая. По рынку о Верховном суде после слушаний 05.11.2025 сообщали об объёме более $1.3M суммарно на двух площадках, вероятность ~25–29% **[вероятно]**. Исход и дату решения я **не проверил**.
5. **Крипто-регулирование / Strategic Bitcoin Reserve.** Рынок «SBR в 2025» дошёл до пика ~77% в марте 2025 и закрылся на ~1% при объёме ~$5M **[вероятно]**. Методологический урок: указ о SBR подписан 06.03.2025, но без покупок, и BTC на этой новости упал **[вероятно, по памяти — проверить]**. Значит, знак «беты к событию» зависит от формулировки исхода, а не только от того, что событие «про крипту».
6. **Шатдаун правительства.** Kalshi в октябре 2025 — около $13M по рынку длительности; февраль 2026 — ~$18M на каждой площадке **[вероятно]**. Связь с BTC слабая и косвенная (через данные: шатдаун задерживает релизы CPI и NFP).
7. **Выборы** (2024, промежуточные выборы в ноябре 2026). Классический «Trump trade» 2024 года: корреляция вероятности Trump на Polymarket с BTC видна на дневных данных **[вероятно]** (Blockscholes, Coin Metrics), но формальных intraday-оценок я не нашёл.

**Kalshi как второй источник**: регулируется CFTC, есть публичное REST API со свечами и сделками. Данные разделены на live- и historical-уровни: `GET /historical/markets/{ticker}/candlesticks`, `GET /historical/trades`, граница уровней — `GET /historical/cutoff` **[подтв.]**, docs.kalshi.com. Fed-рекомендация: Diercks, Katz, Wright, «Kalshi and the Rise of Macro Markets» (FEDS 2026-010). Модальный прогноз Kalshi накануне FOMC был точен во всех случаях выборки и статистически лучше fed funds futures. По headline CPI Kalshi лучше консенсуса Bloomberg **[подтв.]** по аннотации и пересказам. Есть версия от сентября 2026, цифры могли поменяться. Наличие двух площадок даёт **естественную проверку**: шок, который виден на обеих, — информация, а шок на одной — шум ликвидности.

**Предупреждения о ликвидности:**
- Wash trading на Polymarket (Columbia, SSRN, ноябрь 2025) — около 25% исторического объёма. По категориям: спорт 45%, выборы 17%, политика 12%, крипто 3% **[подтв.]** по препринту. Объём как прокси ликвидности поэтому ненадёжен. Брать глубину стакана и спред, а не volume.
- Кривая калибровки: favourite–longshot bias на Kalshi (Bürgi et al., 2025, VoxEU). Есть и «underconfidence» политических рынков: цены сжаты к 50% (arXiv 2602.19520) **[вероятно]**. Изменение цены в хвостах (p < 0.1, p > 0.9) не равно изменению вероятности, нужна поправка.

## 2. Truth Social, BTC и что быстрее

**Эмпирика по эпизодам:**
- **09.04.2025**: пост «THIS IS A GREAT TIME TO BUY!!! DJT» в 9:37 ET, пауза тарифов на 90 дней объявлена в Truth Social в 13:18 ET **[подтв.]**, Reuters, NPR. Reuters отмечал крупные опционные ставки за минуты до поста **[подтв.]**, что инсайдом это не доказывает.
- **10.10.2025**: утренний пост с угрозой тарифов против Китая (~14:57 UTC по одному источнику) **[вероятно]**. Затем после закрытия рынков США — пост про +100% тарифов с 1 ноября. BTC сразу потерял ~$3k, затем упал на 12–14% от $122.5k. Около $19.1B ликвидаций за 24 часа по CoinGlass **[подтв.]** по нескольким источникам. Каскад ликвидаций, по Amberdata, около 20:50 UTC **[вероятно]**. Точную минуту второго поста я **не подтвердил**, её надо снять с trumpstruth.org. Эпизод загрязнён микроструктурой (депег USDe на Binance до $0.66, споры о ценовых оракулах Binance), это не чистый сигнал «новости».
- **Номинация Warsh (январь 2026)**: Polymarket и Kalshi сдвинулись **за день до** поста (39% → 95%) на утечках в прессе. BTC двигался параллельно **[вероятно]**. Это кандидат на эпизод, где prediction market мог опережать.
- **Insider-ставки на Polymarket**: перед поимкой Maduro (январь 2026) вероятность ползла 6.5% → 11% до полуночи, ещё до новостей. Перед перемирием с Ираном (апрель 2026) по данным Dune минимум 50 свежих кошельков поставили «Yes» за часы до поста в ~18:30 ET **[подтв.]**, AP и Euronews. Для статьи это аргумент: информационное преимущество Polymarket сосредоточено в **предварительных утечках**, а не в реакции на публичные посты.

**Литература по сигналам из соцсетей:**
- **Ante (2023)**, TFSC 186, 122112: 47 крипто-твитов Musk. Аномальные доходности и объёмы значимы, но цена значима только для DOGE. По BTC положительные и отрицательные эффекты гасят друг друга, хотя отдельные твиты давали +16.9% / −11.8% **[подтв.]** по аннотации. Урок для нас: без знака или классификатора средний эффект размывается. Это аргумент за LLM-классификатор направления.
- **Bianchi, Gómez-Cram, Kind, Kung (2023, JME)**, «Threats to central bank independence: high-frequency identification with Twitter». Тиковые fed funds futures в узком окне вокруг твитов Trump о ФРС, эффект около −10 bp (пик −18.5 bp) **[подтв.]**. **Это главный методологический образец**: high-frequency identification с меткой времени поста как событием.
- Krause (SSRN): Trump-события про крипту и избыточная доходность BTC, 5 событий **[вероятно]**. Слабая работа. Студенческая работа из Лунда — дневной OLS и VADER. Серьёзного intraday event study «Truth Social → BTC» за 2025–2026 **я не нашёл**: это пробел.
- Proxy-latency: OpenMarket (Young, arXiv 2607.26245). Котировки Polymarket по BTC-рынкам реагируют на крупные движения Binance с медианой **347 мс**. Прогнозная модель из 43 микроструктурных признаков не обгоняет цену стакана Polymarket **[подтв.]**. Значит, на собственных BTC-рынках Polymarket **ведомый**, а Binance — ведущий. Для макро-рынков с более тонкой ликвидностью лаг должен быть больше **[не подтв.]**, это гипотеза для проверки.

**Идентификация (ядро статьи).** Пусть `N_t` — публичный сигнал (пост). Наблюдаем `Δp_t` (Polymarket) и `r_t` (BTC). Если оба реагируют на `N_t` с лагами `τ_p` и `τ_b`, то при `τ_b < τ_p` BTC «ведёт», а при `τ_p < τ_b` «ведёт» Polymarket. В обоих случаях это **не** информационное преимущество, а разная скорость обработки общего фактора. Отсюда схема:
1. Строим индекс событий-постов с точным временем (секунды) и отдельно сигнал заголовков в ленте новостей (вторичное распространение).
2. **Условный lead-lag**: оцениваем опережение Polymarket → BTC в окнах **без** постов и новостей (Polymarket как источник информации) и отдельно в окнах вокруг постов (общий фактор, сравнение скоростей).
3. Ортогонализация: `Δp_t^⊥ = Δp_t − E[Δp_t | N_{t−k..t}, r_{t−k..t}]`. Только остаток шока вероятности тестируется как предиктор `r_{t+h}`.
4. Классификация шоков: (a) пост или новость предшествует, (b) ничего публичного нет, это утечка или order flow, (c) шум (отразился на одной площадке, тонкий стакан, быстрый откат).

Гипотеза, которую стоит проверить и которую можно сформулировать заранее: **парсер Truth Social → BTC** быстрее любого пути через Polymarket. Prediction markets несут добавочную информацию только в классе (b) и в «медленных» вопросах: номинации, переговоры, шатдаун.

## 3. Литература (ядро)

**Рынки предсказаний как агрегаторы информации**
- Wolfers & Zitzewitz (2004), «Prediction Markets», *JEP* 18(2). (2006) — «Interpreting Prediction Market Prices as Probabilities», NBER w12200: условия, при которых цена ≈ средняя вероятность.
- **Snowberg, Wolfers, Zitzewitz (2007)**, «Partisan Impacts on the Economy: Evidence from Prediction Markets and Close Elections», *QJE* 122(2). Высокочастотная реакция фьючерсов на изменение вероятности победы в ночь выборов 2004, наклон ΔlogP / Δp. Это прямой прототип «беты к событию».
- **Snowberg, Wolfers, Zitzewitz (2011)**, «How Prediction Markets Can Save Event Studies», NBER w16949. Результат event study зависит от окна, априорной вероятности и загрязнения окна. Вероятности рынков предсказаний решают все три проблемы **[подтв.]**.
- Свежие работы по Polymarket и Kalshi:
  - Ng, Peng, Tao, Zhou, «Price Discovery and Trading in Modern Prediction Markets» (SSRN 5331995, 2025, ревизия 2026). Polymarket ведёт Kalshi в price discovery, особенно при высокой ликвидности **[подтв.]** по аннотации и семинару.
  - Aktuğ & Torul (2026): 9 платформ на выборах 2024, инструменты price discovery из рынков акций. Polymarket ведёт на 5-минутной частоте, Betfair — на часовой **[вероятно]**.
  - Tsang & Yang (arXiv 2603.03152): политические шоки 2024 года, Kyle-λ и разложение Glosten–Harris. Дебаты — транзитный скачок с откатом, покушение — перманентная переоценка **[подтв.]**. Это готовый инструмент «шок информативный или транзитный».
  - arXiv 2604.24147: дисбаланс крупных сделок предсказывает доходности между платформами **[вероятно]**.
  - Diercks–Katz–Wright (FEDS 2026-010) и Angelini (arXiv 2606.30040) — см. п.1.
  - Young, OpenMarket (arXiv 2607.26245) — см. п.2.

**Lead-lag и price discovery**
- Hasbrouck (1995), «One Security, Many Markets», *JF* 50(4) — information share.
- Gonzalo & Granger (1995), *JBES* 13(1) — component share. Putniņš (2013), «What do price discovery metrics really measure?», *JEF*: IS и CS смешивают скорость и шум. Рекомендует Information Leadership Share (Yan & Zivot 2010). **Для нас это критично**: у Polymarket шум выше, наивный IS занижает или искажает его вклад.
- Проблема: BTC и вероятность — не одна бумага, коинтеграции 1:1 нет. Решение: работать с **ожидаемой доходностью BTC, подразумеваемой вероятностью**: `π_t = β̂ · p_t`. Тогда пара (log BTC, π_t) в окне события — две «цены» одной информации, и к ней применимы IS/ILS. Это адаптация, а не готовая методика **[не подтв.]**, надо обосновать.
- Hayashi & Yoshida (2005) — ковариация для несинхронных наблюдений. Hoffmann, Rosenbaum, Yoshida (2013), *Bernoulli* — оценка lead-lag по несинхронным тикам. Подходит под редкие сделки Polymarket и тики Binance.

**High-frequency event studies**
- Gürkaynak, Sack, Swanson (2005), *IJCB* 1(1) — факторы target и path по 30-минутным окнам. Nakamura & Steinsson (2018), *QJE*. Bauer & Swanson (2023, NBER w29939) — ортогонализация сюрпризов к данным до объявления.
- Крипто и ФРС: Kyriazis et al. (arXiv 2302.10252): сюрпризы ФРС бьют BTC и ETH, волатильность 5-минутных доходностей растёт на FOMC. NY Fed Staff Report 1052: BTC почти не реагирует на сюрприз короткой ставки, реакция на path неустойчива. Работа в *Annals of Finance* (s10436-023-00432-3): реакция меняет знак во времени **[вероятно]** по аннотациям. Вывод: **бета BTC к макро-событиям нестационарна**, её надо оценивать скользящим окном или с режимами.
- Джампы: Lee & Mykland (2008), *RFS* 21(6). Barndorff-Nielsen & Shephard (2006), *J. Fin. Econometrics* 4(1). Aït-Sahalia & Jacod (2009), *AoS*.
- Hawkes: Bacry, Mastromatteo, Muzy (2015), «Hawkes processes in finance», *Market Microstructure and Liquidity*. Phillips & Gorse (2018) — взаимное возбуждение доходностей крипты и тем соцсетей. Работы по Hawkes для скачков VIX и BTC (бипауэр-вариация + 4-мерный Hawkes) **[вероятно]**.
- Локальные проекции: Jordà (2005), *AER* 95(1).

## 4. Как сделать математичнее

**4.1 Определение шока.** Работать в логит-шкале: `x_t = logit(p_t)`. Это снимает сжатие у границ и частично поправку на favourite–longshot. Варианты:
- Порог: `|Δx_t| > k·σ̂_t`, где `σ̂_t` — робастная (бипауэрная) локальная волатильность на скользящем окне, k ∈ {3, 4, 5}.
- **Lee–Mykland** на ряде `x_t` с поправкой на неравномерную сетку (сэмплировать в бизнес-времени по сделкам) и на микроструктурный шум (pre-averaging, Jacod et al. 2009). Это **новое применение**: jump-тесты на вероятностях событий я в литературе не встречал **[не подтв.]**.
- Фильтр «информационности» по Tsang–Yang: шок засчитывается, если ≥ X% скачка сохраняется через h минут (перманентная компонента Glosten–Harris), и/или если он подтверждён второй площадкой (Kalshi) в пределах Δ.
- Фильтр ликвидности: минимальная глубина стакана ±2¢, спред ≤ s, исключить сделки, похожие на wash trading (по сетевому методу Columbia или простые эвристики самосделок).

**4.2 Из вероятности в ожидаемую доходность.** Для бинарного события E:
`E[r_BTC | info] = p·μ_1 + (1−p)·μ_0`, откуда `∂E[r]/∂p = μ_1 − μ_0 ≡ β_E`.
Оценка `β_E` по SWZ (2007): регрессия `r_BTC,[t,t+h]` на `Δp_[t,t+h]` в окнах, где движение вероятности доминирует (ночь выборов, день номинации, релиз CPI). Проверка: при разрешении исхода (p → 0/1) `r ≈ β_E·(1 − p_{t−})`. Это **тест на согласованность**: бета из движения вероятностей до разрешения против беты из скачка при разрешении. Сигнал = `ŝ_t = β̂_E · Δp_t^⊥`. Сравнить с фактической `r_{t+h}`: если BTC «недореагировал», это либо опережение, либо ошибка беты. Для многоисходных рынков (решение ФРС: −50/−25/0/+25) — вектор `β` и `Δp` на симплексе. Естественная мера сюрприза — ожидаемое изменение ставки `Σ_k Δp_k · k` (аналог сюрприза fed funds futures по Kuttner).

**4.3 Динамика.**
- VAR / VECM на сетке 1–5 мин: (Δx_Poly, Δx_Kalshi, r_BTC, индикатор поста). Импульсные отклики + IS/ILS.
- **Локальные проекции**: `r_{t→t+h} = α_h + θ_h·shock_t + γ_h'controls + ε` для h = 1…60 мин. Шоки — ортогонализированные Δx и dummy постов. Отдельно класс (b) «без публичной новости».
- **Многомерный Hawkes**: события = {пост Trump (по классам LLM), скачок Polymarket ↑/↓, джамп BTC ↑/↓}. Ядро `φ_{ij}(t)` (экспоненциальное или непараметрическое по Bacry–Muzy). Ветвящаяся матрица `‖φ_{ij}‖` прямо отвечает на вопрос «кто кого возбуждает и с каким лагом» и учитывает общий драйвер (пост) как отдельную размерность. Это самая чистая формализация идентификационной проблемы.
- Нестационарность: rolling β, или Markov-switching β по режимам «тарифный» / «ФРС» / «спокойный».

**4.4 Текстовый сигнал.** Парсер Truth Social → LLM-классификатор: тема (тарифы / ФРС / крипта / геополитика / прочее), направление для BTC (+ / − / 0), «новизна» (повтор или новое заявление), уверенность. Это решает проблему Ante (усреднение разных знаков). Для научной части:
- Заморозить промпт и модель, выложить разметку. Проверить согласие с ручной разметкой (κ Коэна) на 200–300 постах.
- **Look-ahead**: LLM не должна знать, что было потом. Использовать модель с отсечкой знаний до начала выборки или проверять устойчивость на постах после отсечки.
- Сравнить три канала: пост → BTC, пост → Polymarket → BTC, Polymarket без поста → BTC. Для каждого — распределение лагов и доля объяснённой дисперсии.

**4.5 Оценка «полезности» без торговой рамки.** Метрики прогноза (корреляция знака, R² out-of-sample, Diebold–Mariano против бенчмарка «цена стакана уже всё знает», как в OpenMarket). Издержки и PnL — только как приложение «экономическая значимость» с консервативными комиссиями и проскальзыванием.

## 5. Данные

- **Polymarket**:
  - CLOB `GET /prices-history`: параметры `market` (token id), `startTs`, `endTs`, `interval` ∈ {1m, 1h, 6h, 1d, 1w, max, all}, `fidelity` (минуты, по умолчанию 1); ответ — `{history:[{t,p}]}` **[подтв.]**, docs.polymarket.com. Гранулярность ≥ 1 минута. Это mid или last, а не сделки.
  - Сделки с точностью до секунды: on-chain события OrderFilled (Polygon). **Внимание**: 28.04.2026 Polymarket перешёл на v2-контракты, и публичные сабграфы Goldsky отдают неполные данные. Goldsky рекомендует Turbo Pipelines **[подтв.]**, docs.goldsky.com. Dune подходит для агрегатов. Есть сторонние датасеты на Hugging Face (SII-WANGZJ/Polymarket_data и др.) **[не проверял качество]**.
  - Метаданные рынков: Gamma API. Стакан в реальном времени — WebSocket CLOB. **Историю стакана придётся собирать самим вперёд**: ретроспективно её нет **[вероятно]**.
- **Kalshi**: REST — свечи (`period_interval`), сделки, historical-уровень. Без ключа частично доступно **[вероятно]**.
- **BTC**: Binance (спот и перпы) — публичные архивы data.binance.vision (aggTrades, klines 1s) **[подтв., общеизвестно]**. Tardis.dev — тики, L2, ликвидации по многим биржам, платно, с бесплатным первым днём месяца **[вероятно]**. Добавить CME BTC futures и Coinbase для проверки на US-часы. Готовый синхронизированный датасет Polymarket–Binance с миллисекундами: OpenMarket (HF `gregyoung14/openmarket-btc-polymarket`, февраль–май 2026), но только по BTC-рынкам, не макро.
- **Truth Social**:
  - **trumpstruth.org** (Defending Democracy Together): архив постов с датой и временем до минуты и ссылкой на оригинал, есть поиск **[подтв.]**. API или выгрузку **не подтвердил**.
  - Сам Truth Social построен на Mastodon. Клиент `truthbrush` (Stanford Internet Observatory, open source) отдаёт `created_at` с точностью до секунды (ISO 8601) **[вероятно]**.
  - Trump Media анонсировала платный «Truth API» с архивом с 2022 года **[вероятно]**, запуск не подтвердил. Также есть Apify-скрейперы.
  - Академический датасет Gerard–Botzer–Weninger (ICWSM 2023) — вся платформа, старый.
  - **Свой парсер из README — главный актив**: собственные метки времени получения поста дают реальную латентность «пост → доступен боту». Её надо сравнить с `created_at`.
- **Новостные метки**: время заголовков (Bloomberg/Reuters недоступны бесплатно). Прокси — популярные агрегаторы заголовков в X/Telegram со своими метками времени **[не подтв. доступность]**.
- **Календарь макро**: время FOMC и CPI (точно 14:00 / 8:30 ET). Сюрпризы — из fed funds futures (CME) или из самого Kalshi.

## 6. Новизна, риски, вердикт

**Новизна.** Свободно: (1) intraday-связь **макро/политических** prediction markets и BTC; (2) jump-тесты и Hawkes на рядах вероятностей; (3) явное разделение «общий драйвер (пост) против собственной информации рынка предсказаний» с собственными метками постов; (4) оценка «беты к событию» для BTC по SWZ. Уже занято: price discovery между prediction markets (Ng et al., Aktuğ–Torul), качество Kalshi-прогнозов (Diercks et al.), Polymarket против Binance на BTC-рынках (OpenMarket), твиты против ставок (Bianchi et al.).

**Риски.**
- *Подача как торговой стратегии.* arXiv q-fin и SSRN такие статьи принимают, но модерация arXiv режет текст «вот прибыльная стратегия» без научного вклада; SSRN мягче **[не подтв., основано на практике]**. Решение: заголовок и вопрос — про **price discovery и информационное содержание**. Например: «Do Prediction Markets Contain Information Not Yet in Bitcoin Prices? Evidence from Macro and Political Event Contracts». Слово «trading signal» убрать из заголовка. PnL — в приложение с издержками. Обязателен null-friendly дизайн: OpenMarket показывает, что честный null публикуем.
- *Малое число событий.* Крупных шоков десятки, а не тысячи. Нужно объединение по типам и бутстрэп или рандомизационные тесты по плацебо-временам.
- *Тонкая ликвидность, wash trading, сдвиги правил* (v2-контракты, комиссии), регуляторная история Polymarket в США — всё это меняет микроструктуру. Нужны подвыборки.
- *Инсайдерская торговля.* Если главный источник опережения — insider-ставки, статья неизбежно касается этики. Подавать нейтрально: «information leakage», со ссылками на AP и Reuters, без обвинений.
- *Нестационарность беты BTC* (смена знака реакции на ФРС, тарифный режим 2025 года).
- *Точность времени*: минутные метки trumpstruth против секундных `created_at`. Без своих секундных меток выводы «кто быстрее» на горизонте < 1 мин ненадёжны.

**Вердикт.**
- **Реализуемость: 4/5.** Все данные доступны бесплатно или дёшево. Узкое место — сделки Polymarket после перехода на v2 и отсутствие истории стакана. Тики BTC с Binance и посты есть.
- **Новизна: 3.5/5.** Сама связка новая, но соседи плотные. Новизна вырастет, если в статье будет Hawkes-разложение «пост / Polymarket / BTC» и jump-тесты на вероятностях.

**Рекомендованная структура статьи:**
1. Introduction: вопрос price discovery; почему вероятности = мера сюрприза (SWZ 2011); вклад — 3 пункта.
2. Related literature: prediction markets → price discovery → HF event studies → social media и крипта.
3. Data: рынки (таблица ликвидности, фильтры), BTC-тики, корпус Truth Social (метки, LLM-разметка, валидация).
4. Measuring shocks: логит, Lee–Mykland/BNS, фильтры перманентности и подтверждения второй площадкой.
5. Event betas: β_E по SWZ, согласованность «до разрешения против разрешения».
6. Lead-lag: Hayashi–Yoshida / HRY lead-lag, IS/ILS по паре (log BTC, β·p), отдельно окна с постами и без.
7. Mutual excitation: многомерный Hawkes {пост, скачок PM, джамп BTC}, ветвящаяся матрица.
8. Predictability: локальные проекции, out-of-sample против бенчмарков; экономическая значимость — в приложении.
9. Robustness: Kalshi против Polymarket, подвыборки по ликвидности и периоду, плацебо-времена, другой классификатор.
10. Conclusion: где prediction markets добавляют информацию (утечки, медленные вопросы), а где лишь эхо поста.

---

## Источники

- Young, OpenMarket: A Synchronized Polymarket–Binance Dataset (arXiv 2607.26245) — https://arxiv.org/abs/2607.26245
- Ng, Peng, Tao, Zhou, Price Discovery and Trading in Modern Prediction Markets (SSRN 5331995) — https://papers.ssrn.com/abstract=5331995 ; семинар — https://fss.um.edu.mo/?p=51244
- Aktuğ & Torul (2026), price discovery 9 платформ — https://web.bogazici.edu.tr/torul/pridis.pdf
- Tsang & Yang, Political Shocks and Price Discovery in Prediction Markets (arXiv 2603.03152) — https://arxiv.org/abs/2603.03152
- Price as Focal Point (arXiv 2604.24147) — https://arxiv.org/pdf/2604.24147
- Prices as probabilities, Kalshi+Polymarket 353M сделок (arXiv 2602.19520) — https://www.alphaxiv.org/abs/2602.19520
- Diercks, Katz, Wright, Kalshi and the Rise of Macro Markets (FEDS 2026-010) — https://www.federalreserve.gov/econres/feds/files/2026010pap.pdf ; версия ECB 2026 — https://www.ecb.europa.eu/press/conferences/shared/pdf/20261005_monpolconf/Wright_paper.pdf
- Angelini, The Shape of Macroeconomic Beliefs (arXiv 2606.30040) — https://arxiv.org/abs/2606.30040
- VoxEU, The economics of the Kalshi prediction market (Bürgi et al.) — https://cepr.org/voxeu/columns/economics-kalshi-prediction-market
- Columbia, Network-Based Detection of Wash Trading (Polymarket) — https://gamblingharm.org/wp-content/uploads/2025/11/Polymarket-Wash-Trading-Study.pdf ; Fortune — https://fortune.com/2025/11/07/polymarket-wash-trading-inflated-prediction-markets-columbia-research
- Snowberg, Wolfers, Zitzewitz, How Prediction Markets Can Save Event Studies (NBER w16949) — https://www.nber.org/papers/w16949.pdf
- Snowberg, Wolfers, Zitzewitz (2007), Partisan Impacts on the Economy, QJE 122(2) — https://doi.org/10.1162/qjec.122.2.807
- Wolfers & Zitzewitz (2004), Prediction Markets, JEP — https://www.aeaweb.org/articles?id=10.1257/0895330041371321
- Bianchi, Gómez-Cram, Kind, Kung, Threats to Central Bank Independence (NBER w26308 / JME 2023) — https://www.nber.org/system/files/working_papers/w26308/w26308.pdf
- Ante (2023), How Elon Musk's Twitter activity moves cryptocurrency markets, TFSC 186 — https://ideas.repec.org/a/eee/tefoso/v186y2023ipas0040162522006333.html
- Kyriazis et al., Monetary Policy, Digital Assets, and DeFi Activity (arXiv 2302.10252) — https://arxiv.org/abs/2302.10252
- NY Fed Staff Report 1052 — https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr1052.pdf
- Bitcoin и шоки ЦБ (Annals of Finance) — https://link.springer.com/article/10.1007/s10436-023-00432-3
- Bauer & Swanson (NBER w29939) — https://www.nber.org/papers/w29939
- Gürkaynak, Sack, Swanson (2005), IJCB — https://www.ijcb.org/journal/ijcb05q2a2.htm
- Hasbrouck (1995), JF — https://doi.org/10.1111/j.1540-6261.1995.tb04054.x ; Gonzalo & Granger (1995), JBES — https://doi.org/10.1080/07350015.1995.10524581 ; Putniņš (2013), JEF — https://doi.org/10.1016/j.jempfin.2013.01.001
- Lee & Mykland (2008), RFS — https://doi.org/10.1093/rfs/hhm056 ; Barndorff-Nielsen & Shephard (2006) — https://doi.org/10.1093/jjfinec/nbi022
- Bacry, Mastromatteo, Muzy (2015), Hawkes processes in finance — https://arxiv.org/abs/1502.04592 ; Phillips & Gorse (2018) — https://discovery-pp.ucl.ac.uk/id/eprint/10074781
- Jordà (2005), Local Projections, AER — https://doi.org/10.1257/0002828053828518
- Hoffmann, Rosenbaum, Yoshida (2013), lead-lag estimation — https://arxiv.org/abs/1104.5466
- Polymarket prices-history API — https://docs.polymarket.com/api-reference/markets/get-prices-history.md ; blockchain data — https://docs.polymarket.com/resources/blockchain-data
- Goldsky, Polymarket (v2, сабграфы) — https://docs.goldsky.com/chains/polymarket
- Kalshi historical data — https://docs.kalshi.com/getting_started/historical_data
- Trump's Truth (архив) — https://trumpstruth.org ; Truth API (Engadget) — https://engadget.com/2217943/there-s-now-an-api-for-mainlining-trump-s-truth-social-posts ; Truth Social dataset (ICWSM 2023) — https://ar5iv.labs.arxiv.org/html/2303.11240
- 09.04.2025 пауза тарифов: NPR — https://www.npr.org/2025/04/16/1245044457/did-trump-enable-insider-trading ; Reuters через Nation Thailand — https://www.nationthailand.com/news/world/40048638
- 10.10.2025: CoinGecko — https://www.coingecko.com/learn/october-10-crypto-crash-explained ; Bloomberg Gov — https://news.bgov.com/crypto/crypto-sees-more-than-3-billion-in-liquidations-in-past-hour ; Bitcoin Magazine — https://bitcoinmagazine.com/news/bitcoin-price-crashes-to-108000-as-trump-to-impose-100-tariffs-on-china/embed
- Warsh: The Block — https://www.theblock.co/post/387788/kevin-warsh-polymarket-odds-fed-chair ; https://www.theblock.co/post/387819/trump-names-crypto-friendly-kevin-warsh-as-pick-for-fed-chair
- Insider-ставки: Al Jazeera — https://aljazeera.com/news/2026/3/25/large-polymarket-wall-street-bets-on-trumps-war-news-under-scrutiny ; Euronews/AP — https://www.euronews.com/2026/04/09/newly-made-polymarket-accounts-won-massively-on-us-iran-ceasefire-bets ; Maduro — https://www.business-standard.com/amp/world-news/trader-made-410000-betting-us-capture-nicolas-maduro-126010601151_1.html
- Объёмы FOMC-рынков: Cryptoast — https://cryptoast.fr/220-millions-dollars-volume-decision-fed-fait-exploser-paris-polymarket/ ; polyguana — https://polyguana.com/resolved/601699
- SBR-рынок: The Block — https://theblock.co/post/335727/polymarket-predicts-55-chance-trump-will-create-a-strategic-bitcoin-reserve-during-his-first-100-days ; HTX — https://www.htx.com/en-in/news/polymarket-odds-of-a-us-crypto-reserve-in-2025-plummet-by-98-epruChP5/
- IEEPA и Верховный суд: Econbrowser — https://econbrowser.com/archives/2025/11/betting-on-noise-supreme-court-and-ieepa-tariffs
- Шатдаун: Bitcoin.com — https://news.bitcoin.com/prediction-markets-bet-big-on-us-government-dysfunction-shutdown-odds-stretch-toward-thanksgiving/
- Kalshi объёмы: DeFi Rate — https://defirate.com/?p=9002 ; The Block — https://www.theblock.co/post/371287/kalshi-surges-past-polymarket-in-volume-grabs-global-dominance
- Trump trade 2024: Coin Metrics — https://coinmetrics.substack.com/p/state-of-the-network-issue-284 ; Blockscholes — https://blockscholes.com/premium-research/us-election-2024-onchain-insight
