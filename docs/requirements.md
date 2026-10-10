# Requirements Specification

## 1. Project Overview & Business Problem

International e-commerce retailers and brand managers struggle to achieve real-time visibility into cross-border competitor pricing and market positioning. While product listings appear in various local currencies across regional marketplaces (such as Amazon US, Amazon UK, Amazon IN, Flipkart, and specialized verticals), the raw sticker price fails to reflect the **true landed cost** to the consumer or the seller's true competitive margin. 

Key challenges include:
- Disparate regional currencies and fluctuating foreign exchange rates.
- Cross-border logistics (international freight, local last-mile delivery, insurance).
- Customs duties, import tariffs, and destination taxes (VAT, GST, de minimis thresholds).
- Identifying identical or comparable products across disparate catalogs with varied titles and missing SKUs.
- Detecting rapid competitor price shifts and market entry opportunities.

This project delivers a **Real-Time Web Scraping Engine for Cross-Border E-Commerce Pricing Intelligence and Market Positioning**, providing automated data extraction, product matching, landed cost modeling, historical tracking, competitor intelligence, and interactive visual analytics.

---

## 2. Functional Requirements (FR)

### FR-1: Product & Catalog Management
- Maintain a canonical catalog of tracked master products (`Product`).
- Support categorization, brand identification, SKU/GTIN/UPC metadata, and base reference pricing.
- Manage marketplace entities (`Marketplace`) and geographic market profiles (`Country`).

### FR-2: Configurable Ingestion & Dataset Discovery
- **Data Ingestion Module**: Import external datasets (CSV/JSON) with schema validation, normalization, and provenance tracking.
- **Sample/Public API Connector**: Ingest standardized sample feeds (DummyJSON, FakeStore) for reproducible benchmarking and offline testing.
- Differentiate data provenance: `live_scrape`, `imported_dataset`, `demo_api`, and `synthetic_seed`.

### FR-3: Responsible Web Scraping Engine
- Pluggable scraper adapter architecture (`BaseScraperAdapter`).
- Support for target-specific HTML parsing, structured extraction (title, price, currency, availability, rating, URL), and sanitization.
- Concurrency control, rate limiting, token buckets, and jittered exponential backoff.
- Strict SSRF (Server-Side Request Forgery) protection blocking loopback, private RFC1918, link-local, and cloud metadata endpoints (`169.254.169.254`).
- Compliance with `robots.txt`, public page restrictions, and error logging without bypassing CAPTCHA or access controls.

### FR-4: Cross-Marketplace Product Matching
- Cross-listing resolution using multi-factor similarity:
  - Exact identifier matching (SKU, GTIN, ASIN, Model Number).
  - Normalized token similarity and Levenshtein fuzzy distance.
  - Brand and category alignment.
- Categorization into match confidence tiers:
  - **Confirmed Match** ($\ge 85\%$)
  - **Probable Match** ($65\% - 84\%$)
  - **Uncertain Match** ($< 65\%$)
- Administrative interface to verify, confirm, or decouple match pairs.

### FR-5: Currency Normalization & Landed-Cost Engine
- Dynamic foreign exchange rate retrieval via traceable public APIs (`open.er-api.com` / Frankfurter) with cached fallbacks.
- Configurable landed cost computation including:
  - Product price converted to destination currency.
  - Freight and handling charges.
  - Insurance fees.
  - Customs duties based on product category, destination country, and de minimis exemptions.
  - Import taxes (VAT/GST/Sales tax) applied on CIF + Duty.
- Full provenance and transparent audit trail for all calculation assumptions.

### FR-6: Historical Price Tracking & Observation Storage
- Immutable price observation records (`PriceObservation`) with exact capture timestamp.
- Computation of periodic price movements, running minimum/maximum/average prices, and volatility.
- Stale data detection and missing observation handling without recording false zeros.

### FR-7: Market Positioning Intelligence
- Automated market analytics:
  - Cross-market price disparity and landed cost comparisons.
  - Competitor price gap percentage:
    $$\text{Price Gap \%} = \frac{\text{Our Landed Cost} - \text{Competitor Landed Cost}}{\text{Competitor Landed Cost}} \times 100$$
  - Market median and quintile positioning.
  - Market opportunity index (identifying under-priced or high-margin destination countries).
  - Anomaly detection for unusual discounts or sudden price hikes.

### FR-8: Price Alerting & Notification Engine
- Configurable alert rules:
  - Threshold triggers (e.g., competitor price dropped below \$X).
  - Percentage swing triggers (e.g., price shifted by $>10\%$ in 24 hours).
  - Availability/Stock-out triggers.
  - Landed-cost margin breach triggers.
- State-machine deduplication preventing alert spamming.

### FR-9: Interactive Web Dashboard
- **Overview Dashboard**: High-level KPIs, scraping health, active alerts, and top market opportunities.
- **Product Comparison Matrix**: Cross-border price breakdown, landed cost components, and provenance tags.
- **Historical Trends**: Multi-series interactive time-series charts with date filtering.
- **Market Positioning Matrix**: Competitor benchmarking, median gaps, and automated strategic recommendations.
- **Scraping Operations**: Real-time job executor, status logs, error diagnostics, and source coverage metrics.
- **Alert Center**: Filterable alert log with severity badges and action triggers.
- **System Settings**: Configurable reporting currencies, tax/duty assumptions, and scraper parameters.

### FR-10: Reporting & Data Export
- Export multi-market comparison tables and historical observations to CSV and JSON formats.
- Structured export summaries suitable for executive presentations.

---

## 3. Non-Functional Requirements (NFR)

| Metric | Target | Verification Method |
| :--- | :--- | :--- |
| **Response Latency** | $\le 200\text{ ms}$ for cached API queries; $\le 500\text{ ms}$ for complex landed cost aggregates. | Automated API benchmark tests. |
| **Data Integrity** | $100\%$ traceable exchange rates and calculation formulas; zero silent data corruption. | Mathematical property tests and DB constraints. |
| **Security & SSRF** | Block all requests to loopback (`127.0.0.1`, `::1`), private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local (`169.254.0.0/16`), and AWS/GCP metadata services. | Unit tests against known malicious payload lists. |
| **Modularity** | Decoupled UI, API, Scraper, and Analytics layers. Modular monolith with clean domain service interfaces. | Architecture review & decoupled unit tests. |
| **Reliability & Resilience** | Graceful degradation on network timeout, stale exchange rate indicators, and clear scraping failure reasons. | Fault injection and retry test suite. |

---

## 4. Dataset Discovery & Integration Findings

To ensure realistic cross-border pricing benchmarks and robust ingestion pipelines, the following candidates were evaluated:

| Source Name & URL | Available Fields | Geographic & Market Coverage | Est. Records | History Available? | License / Access | Evaluation & Compatibility |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Open Exchange Rates API** (`https://open.er-api.com/v6/latest/USD`) | Base currency, Target rates (160+ fiat currencies), Timestamp, Next update | Global (160+ countries) | Real-time stream | Rates updated daily; historical rates via endpoint | Open / Free public API (No key required) | **Selected for Live FX**: Provides reliable, traceable currency conversions for multi-currency landed costs. |
| **DummyJSON Products API** (`https://dummyjson.com/products`) | `id`, `title`, `description`, `price`, `discountPercentage`, `rating`, `stock`, `brand`, `category`, `thumbnail`, `images` | US/Global simulated | 194 products | Simulated stock & discounts | MIT / Free Open API | **Selected for Canonical Catalog & Baseline**: Perfect for reproducible product definitions, multi-category benchmarks, and initial seeding. |
| **FakeStore API** (`https://fakestoreapi.com/products`) | `id`, `title`, `price`, `description`, `category`, `image`, `rating` | US/Global e-commerce | 20 products | Static snapshot | Open / Public | **Selected for Cross-Listing Matching Validation**: Clean baseline for fuzzy product matching across alternative catalogs. |
| **Books To Scrape Sandbox** (`https://books.toscrape.com`) | Title, GBP Price, Availability status, Star rating, UPC, Description, Category, Product URL | UK / Global (GBP base) | 1,000 items | Real-time crawlable | Permitted public scraping sandbox | **Selected for Live Scraping Engine**: Dedicated ethical scraping sandbox with deterministic HTML structures, pagination, and real HTTP extraction. |
| **Kaggle Cross-Border E-Commerce Dataset** (`programmer3/cross-border-e-commerce-dataset`) | Transaction ID, Product ID, Price, Discount, Destination Country, Logistics fee | China, US, UK, EU, India | ~50,000 rows | Yes (Transaction log) | Open Data / Research | **Selected for CSV/JSON Ingestion Pipeline**: Ingestion adapter parses and imports historical shipping/price data. |

---

## 5. User Personas & Use Cases

1. **Cross-Border E-Commerce Merchant**: Evaluates target pricing in UK, US, and India to determine profitable export prices taking into account local VAT and import customs.
2. **Pricing Strategist / Category Manager**: Monitors competitor price reductions and sets automated alerts to protect market share.
3. **Data & Business Analyst**: Exports historical price volatility reports and audits landed cost assumptions across international retail channels.
