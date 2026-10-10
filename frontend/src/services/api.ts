/**
 * API Service Client for Cross-Border Pricing Intelligence Backend
 */

import {
  AlertNotificationResponse,
  DashboardSummaryResponse,
  ExportOpportunitiesResponse,
  LandedCostBreakdown,
  LandedCostConfigDTO,
  PriceAlertResponse,
  PriceAnomalyDTO,
  ProductCatalogItem,
  ProductComparisonMatrix,
  ProductHistoryResponse,
  ProductPositioningResponse,
  ScraperAdapterInfo,
  ScrapingJobResponse,
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({}));
      throw new Error(errorBody?.error?.message || `HTTP ${res.status}: ${res.statusText}`);
    }

    const json = await res.json();
    return json.data !== undefined ? json.data : json;
  } catch (err: any) {
    console.warn(`API request to ${endpoint} failed:`, err.message);
    throw err;
  }
}

export const apiClient = {
  // 0. Canonical Product Catalog
  async listCatalogProducts(): Promise<ProductCatalogItem[]> {
    return fetchJson<ProductCatalogItem[]>('/pricing/products');
  },

  // 1. Executive Dashboard KPIs
  async getDashboardSummary(): Promise<DashboardSummaryResponse> {
    return fetchJson<DashboardSummaryResponse>('/dashboard/summary');
  },

  // 2. Cross-Border Comparison Matrix
  async getComparisonMatrix(
    productId: string,
    destinationCountry: string = 'US',
    reportingCurrency: string = 'USD'
  ): Promise<ProductComparisonMatrix> {
    return fetchJson<ProductComparisonMatrix>(
      `/pricing/comparison?product_id=${encodeURIComponent(productId)}&destination_country=${encodeURIComponent(
        destinationCountry
      )}&reporting_currency=${encodeURIComponent(reportingCurrency)}`
    );
  },

  // 3. Landed Cost Simulation
  async simulateLandedCost(payload: {
    price: number;
    source_currency: string;
    destination_country: string;
    product_category?: string;
    override_freight?: number;
    override_duty_rate?: number;
    override_tax_rate?: number;
    override_insurance_rate?: number;
    override_handling_fee?: number;
  }): Promise<LandedCostBreakdown> {
    return fetchJson<LandedCostBreakdown>('/pricing/landed-cost/calculate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // 4. Landed Cost Trade Tariffs Configs
  async getLandedCostConfigs(): Promise<LandedCostConfigDTO[]> {
    return fetchJson<LandedCostConfigDTO[]>('/pricing/configs');
  },

  async updateLandedCostConfig(
    countryId: string,
    payload: Partial<LandedCostConfigDTO>
  ): Promise<LandedCostConfigDTO> {
    return fetchJson<LandedCostConfigDTO>(`/pricing/configs/${countryId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  // 5. Historical Price Tracking & Analytics
  async getProductPriceHistory(
    productId: string,
    reportingCurrency: string = 'USD',
    days: number = 30
  ): Promise<ProductHistoryResponse> {
    return fetchJson<ProductHistoryResponse>(
      `/pricing/history/${encodeURIComponent(productId)}?reporting_currency=${encodeURIComponent(
        reportingCurrency
      )}&days=${days}`
    );
  },

  // 6. Market Positioning & Strategic Pricing
  async getProductPositioning(
    productId: string,
    destinationCountry: string = 'US',
    reportingCurrency: string = 'USD'
  ): Promise<ProductPositioningResponse> {
    return fetchJson<ProductPositioningResponse>(
      `/intelligence/positioning?product_id=${encodeURIComponent(productId)}&destination_country=${encodeURIComponent(
        destinationCountry
      )}&reporting_currency=${encodeURIComponent(reportingCurrency)}`
    );
  },

  // 7. Cross-Border Arbitrage Opportunities
  async getExportOpportunities(
    minMarginPct: number = 5.0,
    reportingCurrency: string = 'USD'
  ): Promise<ExportOpportunitiesResponse> {
    return fetchJson<ExportOpportunitiesResponse>(
      `/intelligence/opportunities?min_margin_pct=${minMarginPct}&reporting_currency=${encodeURIComponent(
        reportingCurrency
      )}`
    );
  },

  // 8. Price Anomalies
  async getPriceAnomalies(
    productId?: string,
    thresholdPct: number = 15.0
  ): Promise<PriceAnomalyDTO[]> {
    const q = productId ? `?product_id=${encodeURIComponent(productId)}&threshold_pct=${thresholdPct}` : `?threshold_pct=${thresholdPct}`;
    return fetchJson<PriceAnomalyDTO[]>(`/intelligence/anomalies${q}`);
  },

  // 9. Scraping Operations
  async listScraperAdapters(): Promise<ScraperAdapterInfo[]> {
    return fetchJson<ScraperAdapterInfo[]>('/scraping/adapters');
  },

  async triggerScrapingJob(payload: {
    marketplace_id: string;
    category?: string;
    max_pages?: number;
    delay_seconds?: number;
  }): Promise<ScrapingJobResponse> {
    return fetchJson<ScrapingJobResponse>('/scraping/jobs', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getScrapingJob(jobId: string): Promise<ScrapingJobResponse> {
    return fetchJson<ScrapingJobResponse>(`/scraping/jobs/${encodeURIComponent(jobId)}`);
  },

  // 10. Alerts & Notifications
  async listAlerts(productId?: string, activeOnly: boolean = false): Promise<PriceAlertResponse[]> {
    const params = new URLSearchParams();
    if (productId) params.append('product_id', productId);
    if (activeOnly) params.append('active_only', 'true');
    const qs = params.toString() ? `?${params.toString()}` : '';
    return fetchJson<PriceAlertResponse[]>(`/alerts${qs}`);
  },

  async createAlert(payload: {
    product_id: string;
    alert_type: string;
    condition_value: number;
    severity?: string;
  }): Promise<PriceAlertResponse> {
    return fetchJson<PriceAlertResponse>('/alerts', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async deleteAlert(alertId: string): Promise<void> {
    await fetchJson<any>(`/alerts/${encodeURIComponent(alertId)}`, {
      method: 'DELETE',
    });
  },

  async evaluateAlerts(productId?: string): Promise<any> {
    const q = productId ? `?product_id=${encodeURIComponent(productId)}` : '';
    return fetchJson<any>(`/alerts/evaluate${q}`, {
      method: 'POST',
    });
  },

  async listNotifications(unacknowledgedOnly: boolean = false): Promise<AlertNotificationResponse[]> {
    const q = unacknowledgedOnly ? '?unacknowledged_only=true' : '';
    return fetchJson<AlertNotificationResponse[]>(`/alerts/notifications${q}`);
  },

  async acknowledgeNotification(notificationId: string): Promise<AlertNotificationResponse> {
    return fetchJson<AlertNotificationResponse>(`/alerts/notifications/${encodeURIComponent(notificationId)}/read`, {
      method: 'PATCH',
    });
  },

  // 11. Report Export URLs
  getComparisonExportUrl(destinationCountry: string = 'US', reportingCurrency: string = 'USD'): string {
    return `${API_BASE_URL}/reports/export/comparison/csv?destination_country=${destinationCountry}&reporting_currency=${reportingCurrency}`;
  },

  getHistoryExportUrl(productId: string, reportingCurrency: string = 'USD', days: number = 30): string {
    return `${API_BASE_URL}/reports/export/history/${productId}/csv?reporting_currency=${reportingCurrency}&days=${days}`;
  },

  getOpportunitiesExportUrl(minMarginPct: number = 5.0, reportingCurrency: string = 'USD'): string {
    return `${API_BASE_URL}/reports/export/opportunities/csv?min_margin_pct=${minMarginPct}&reporting_currency=${reportingCurrency}`;
  },
};
