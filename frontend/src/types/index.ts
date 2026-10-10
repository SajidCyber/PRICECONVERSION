/**
 * Frontend TypeScript Type Definitions
 * Synchronized with FastAPI Backend Pydantic DTOs
 */

export interface APIResponse<T> {
  success: boolean;
  data: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    total?: number;
    limit?: number;
    offset?: number;
  };
}

export interface Country {
  id: string;
  name: string;
  currency_code: string;
  currency_symbol: string;
  default_import_duty_rate: number;
  default_import_tax_rate: number;
  default_de_minimis: number;
  region: string;
}

export interface ExchangeRate {
  id: string;
  base_currency: string;
  target_currency: string;
  rate: number;
  inverse_rate: number;
  source: string;
  is_fallback: boolean;
  fetched_at: string;
}

export interface LandedCostBreakdown {
  original_price: number;
  original_currency: string;
  destination_currency: string;
  fx_rate: number;
  fx_source: string;
  is_fx_fallback: boolean;
  converted_price: number;
  freight_fee: number;
  insurance_fee: number;
  cif_value: number;
  de_minimis_threshold: number;
  is_duty_exempt: boolean;
  customs_duty_rate: number;
  customs_duty_amount: number;
  tax_base_value: number;
  import_tax_rate: number;
  import_tax_amount: number;
  handling_fee: number;
  total_landed_cost: number;
  effective_markup_pct: number;
  assumptions_log: Record<string, any>;
}

export interface ListingComparisonItem {
  listing_id: string;
  marketplace_id: string;
  marketplace_name: string;
  country_id: string;
  country_name: string;
  listing_title: string;
  listing_url: string;
  seller_name?: string;
  availability_status: string;
  rating?: number;
  data_provenance: string;
  last_observed_at?: string;
  original_price: number;
  original_currency: string;
  breakdown: LandedCostBreakdown;
  is_cheapest_sticker: boolean;
  is_cheapest_landed: boolean;
  price_gap_vs_benchmark_pct?: number;
}

export interface ProductComparisonMatrix {
  product_id: string;
  product_sku?: string;
  product_title: string;
  product_brand?: string;
  product_category?: string;
  image_url?: string;
  target_base_price?: number;
  base_currency: string;
  destination_country: string;
  reporting_currency: string;
  total_marketplaces_tracked: number;
  cheapest_marketplace?: string;
  lowest_landed_cost?: number;
  highest_landed_cost?: number;
  landed_cost_spread_pct?: number;
  listings: ListingComparisonItem[];
}

export interface PricePointDTO {
  observation_id: string;
  observed_at: string;
  listed_price: number;
  currency_code: string;
  converted_price: number;
  reporting_currency: string;
  shipping_price: number;
  availability_status: string;
  discount_pct: number;
  data_provenance: string;
}

export interface HistoricalStats {
  current_price: number;
  min_price: number;
  max_price: number;
  avg_price: number;
  absolute_change: number;
  pct_change: number;
  volatility: number;
  observation_count: number;
  first_observed_at: string;
  last_observed_at: string;
  freshness_status: 'fresh' | 'stale' | 'expired';
}

export interface ListingHistorySummary {
  listing_id: string;
  marketplace_id: string;
  marketplace_name: string;
  country_id: string;
  listing_title: string;
  listing_url: string;
  currency_code: string;
  stats: HistoricalStats;
  price_points: PricePointDTO[];
}

export interface ProductHistoryResponse {
  product_id: string;
  product_title: string;
  product_sku?: string;
  reporting_currency: string;
  query_days: number;
  overall_min_converted?: number;
  overall_max_converted?: number;
  overall_avg_converted?: number;
  marketplaces_tracked: number;
  total_observations: number;
  listings_history: ListingHistorySummary[];
  timeline_series: Array<Record<string, any>>;
}

export interface MarketplacePositionDTO {
  listing_id: string;
  marketplace_id: string;
  marketplace_name: string;
  country_id: string;
  original_price: number;
  original_currency: string;
  landed_cost: number;
  reporting_currency: string;
  rank: number;
  price_gap_vs_our_product_pct?: number;
  position_tier: 'cheapest' | 'competitive' | 'premium' | 'overpriced';
  is_our_product: boolean;
  is_cheapest: boolean;
}

export interface PriceAnomalyDTO {
  listing_id: string;
  marketplace_id: string;
  marketplace_name: string;
  product_id: string;
  product_title: string;
  previous_price: number;
  current_price: number;
  pct_change: number;
  anomaly_type: 'price_drop' | 'price_spike';
  detected_at: string;
  severity: 'medium' | 'high' | 'critical';
}

export interface ProductPositioningResponse {
  product_id: string;
  product_title: string;
  destination_country: string;
  reporting_currency: string;
  our_target_landed_cost?: number;
  competitor_median_landed_cost?: number;
  competitor_min_landed_cost?: number;
  competitor_max_landed_cost?: number;
  price_gap_vs_median_pct?: number;
  positioning_index?: number;
  market_competitiveness: 'dominant' | 'highly_competitive' | 'moderately_competitive' | 'uncompetitive';
  strategic_recommendation: string;
  recommendation_reasoning: string;
  total_competitors: number;
  rankings: MarketplacePositionDTO[];
  anomalies: PriceAnomalyDTO[];
}

export interface ExportOpportunityDTO {
  product_id: string;
  product_title: string;
  source_marketplace: string;
  source_country: string;
  source_currency: string;
  source_price: number;
  target_marketplace: string;
  target_country: string;
  target_currency: string;
  target_market_price: number;
  landed_cost_in_target: number;
  reporting_currency: string;
  net_profit_margin: number;
  net_margin_pct: number;
  opportunity_score: number;
  feasibility_rating: 'high' | 'medium' | 'low';
}

export interface ExportOpportunitiesResponse {
  reporting_currency: string;
  min_margin_pct_filter: number;
  total_opportunities_found: number;
  opportunities: ExportOpportunityDTO[];
}

export interface ScrapingHealthDTO {
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  active_jobs: number;
  success_rate_pct: number;
  total_records_extracted: number;
}

export interface DashboardSummaryResponse {
  total_products: number;
  total_marketplaces: number;
  total_listings: number;
  total_observations: number;
  active_alerts_count: number;
  unacknowledged_notifications_count: number;
  total_anomalies_count: number;
  total_export_opportunities_count: number;
  scraping_health: ScrapingHealthDTO;
  recent_activities: Array<{
    type: string;
    title: string;
    message: string;
    timestamp: string;
    severity?: string;
  }>;
}

export interface ProductCatalogItem {
  id: string;
  sku?: string;
  title: string;
  brand?: string;
  category: string;
  image_url?: string;
  target_base_price?: number;
  base_currency: string;
  listings_count: number;
}

export interface ScraperAdapterInfo {
  adapter_name?: string;
  marketplace_id: string;
  marketplace_name?: string;
  country_id?: string;
  base_url: string;
  currency_code?: string;
  is_live_scraper?: boolean;
  supports_categories?: boolean;
  id?: string;
  name?: string;
  type?: string;
  supported_countries?: string[];
  rate_limit_delay_seconds?: number;
  is_active?: boolean;
}

export interface ScrapingJobResponse {
  id: string;
  marketplace_id: string;
  status: string;
  target_category?: string;
  target_url?: string;
  items_discovered: number;
  items_extracted: number;
  error_count: number;
  created_at: string;
  started_at?: string;
  finished_at?: string;
}

export interface PriceAlertResponse {
  id: string;
  product_id: string;
  product_title?: string;
  alert_type: string;
  condition_value: number;
  severity: string;
  is_active: boolean;
  created_at: string;
  notifications_count: number;
}

export interface AlertNotificationResponse {
  id: string;
  alert_id: string;
  product_id?: string;
  product_title?: string;
  observation_id: string;
  alert_type: string;
  severity: string;
  message: string;
  evidence_payload: Record<string, any>;
  is_acknowledged: boolean;
  triggered_at: string;
}

export interface LandedCostConfigDTO {
  id: string;
  country_id: string;
  country_name: string;
  category: string;
  customs_duty_rate: number;
  import_tax_rate: number;
  de_minimis_threshold: number;
  default_freight: number;
  insurance_rate: number;
  handling_fee: number;
  updated_at: string;
}
