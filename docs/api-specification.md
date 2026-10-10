# API Specification (OpenAPI / RESTful)

## 1. Overview & Conventions

The backend exposes a versioned RESTful API under the prefix `/api/v1`. 

- **Data Format**: JSON for requests and responses.
- **Timestamp Format**: ISO 8601 UTC strings (`YYYY-MM-DDTHH:MM:SS.sssZ`).
- **Currency Format**: ISO 4217 standard 3-letter codes (`USD`, `EUR`, `GBP`, `INR`).
- **Pagination**: Standard query parameters `limit` (default 20, max 100) and `offset` (default 0).
- **Standard Envelope**:
```json
{
  "success": true,
  "data": {},
  "meta": {
    "total": 100,
    "limit": 20,
    "offset": 0
  }
}
```

---

## 2. API Endpoints

### 2.1 Products Catalog

#### `GET /api/v1/products`
List canonical tracked products with optional search and category filters.
- **Query Parameters**:
  - `query` (string, optional): Keyword search in title/brand/SKU.
  - `category` (string, optional): Filter by category.
  - `limit` (int, default: 20)
  - `offset` (int, default: 0)
- **Response 200 OK**:
```json
{
  "success": true,
  "data": [
    {
      "id": "prod_a1b2c3d4",
      "sku": "TECH-APL-M3-01",
      "title": "MacBook Pro 14 M3 512GB",
      "brand": "Apple",
      "category": "Electronics",
      "image_url": "https://images.example.com/macbook.jpg",
      "target_base_price": 1599.00,
      "base_currency": "USD",
      "listings_count": 4,
      "created_at": "2026-10-09T12:00:00Z"
    }
  ],
  "meta": { "total": 1, "limit": 20, "offset": 0 }
}
```

#### `POST /api/v1/products`
Create a new canonical product.
- **Request Body**:
```json
{
  "sku": "TECH-APL-M3-01",
  "title": "MacBook Pro 14 M3 512GB",
  "brand": "Apple",
  "category": "Electronics",
  "image_url": "https://images.example.com/macbook.jpg",
  "target_base_price": 1599.00,
  "base_currency": "USD"
}
```

---

### 2.2 Ingestion & Dataset Importers

#### `POST /api/v1/ingestion/import-sample-api`
Ingests verified public catalog items from DummyJSON or FakeStore into canonical products and initial price observations.
- **Request Body**:
```json
{
  "source": "dummyjson",
  "category": "laptops",
  "limit": 10
}
```
- **Response 200 OK**:
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_9876",
    "source_name": "dummyjson_laptops",
    "record_count": 10,
    "inserted_count": 10,
    "duplicate_count": 0,
    "rejected_count": 0
  }
}
```

#### `POST /api/v1/ingestion/upload-csv`
Uploads a CSV dataset containing historical or multi-market listing observations.

---

### 2.3 Web Scraping Operations

#### `GET /api/v1/scraping/adapters`
Returns list of available scraper adapters and their capabilities.

#### `POST /api/v1/scraping/jobs`
Triggers an immediate scraping job for a specified marketplace or category.
- **Request Body**:
```json
{
  "marketplace_id": "books_to_scrape",
  "category": "travel",
  "max_pages": 3
}
```
- **Response 202 Accepted**:
```json
{
  "success": true,
  "data": {
    "job_id": "job_e7f8g9",
    "marketplace_id": "books_to_scrape",
    "status": "queued",
    "queued_at": "2026-10-09T15:30:00Z"
  }
}
```

#### `GET /api/v1/scraping/jobs/{id}`
Returns live status and extraction metrics of a scraping job.

---

### 2.4 Product Matching

#### `GET /api/v1/matching/pairs`
Returns cross-marketplace listing matches for a canonical product with confidence scores and evidence.

#### `POST /api/v1/matching/run`
Triggers automated matching algorithm across unlinked listings.

---

### 2.5 Cross-Border Pricing & Landed Cost

#### `GET /api/v1/pricing/comparison`
Returns comprehensive multi-country, multi-marketplace price and landed-cost matrix for a product.
- **Query Parameters**:
  - `product_id` (string, required)
  - `reporting_currency` (string, default: "USD")
  - `destination_country` (string, default: "US")
- **Response 200 OK**:
```json
{
  "success": true,
  "data": {
    "product_id": "prod_a1b2c3d4",
    "product_title": "MacBook Pro 14 M3 512GB",
    "reporting_currency": "USD",
    "destination_country": "US",
    "listings": [
      {
        "marketplace": "Amazon US",
        "country": "US",
        "original_price": 1599.00,
        "original_currency": "USD",
        "fx_rate": 1.0,
        "converted_price": 1599.00,
        "freight": 0.00,
        "insurance": 0.00,
        "customs_duty": 0.00,
        "import_tax": 0.00,
        "estimated_landed_cost": 1599.00,
        "is_cheapest": true,
        "provenance": "live_scrape",
        "observed_at": "2026-10-09T15:00:00Z"
      },
      {
        "marketplace": "Amazon UK",
        "country": "GB",
        "original_price": 1499.00,
        "original_currency": "GBP",
        "fx_rate": 1.305,
        "converted_price": 1956.19,
        "freight": 25.00,
        "insurance": 19.56,
        "customs_duty": 0.00,
        "import_tax": 0.00,
        "estimated_landed_cost": 2000.75,
        "is_cheapest": false,
        "provenance": "live_scrape",
        "observed_at": "2026-10-09T14:45:00Z"
      }
    ]
  }
}
```

#### `POST /api/v1/pricing/landed-cost/calculate`
Interactive simulator allowing custom override of freight, duty rate, tax rate, and insurance.

#### `GET /api/v1/pricing/history/{product_id}`
Returns historical price time-series aggregated by marketplace.

---

### 2.6 Market Positioning & Intelligence

#### `GET /api/v1/intelligence/positioning`
Returns competitive gaps, median rankings, and actionable pricing recommendations.

---

### 2.7 Alerts & Reports

#### `GET /api/v1/alerts` & `POST /api/v1/alerts`
Manage alert rules.

#### `GET /api/v1/alerts/notifications`
List triggered alert events.

#### `GET /api/v1/reports/export/csv`
Downloads full comparison dataset as a structured CSV.

#### `GET /api/v1/dashboard/summary`
Returns high-level KPI cards, scraping health, active alert counts, and recent price anomalies.
