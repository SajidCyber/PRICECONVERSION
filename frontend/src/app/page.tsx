'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from '@/components/Navbar';
import { Sidebar, TabType } from '@/components/Sidebar';
import { KPICards } from '@/components/KPICards';
import { ComparisonMatrixView } from '@/components/ComparisonMatrixView';
import { PriceHistoryView } from '@/components/PriceHistoryView';
import { MarketPositioningView } from '@/components/MarketPositioningView';
import { ScrapingHubView } from '@/components/ScrapingHubView';
import { LandedCostSimulatorView } from '@/components/LandedCostSimulatorView';
import { AlertCenterView } from '@/components/AlertCenterView';
import { apiClient } from '@/services/api';
import {
  DashboardSummaryResponse,
  ExportOpportunitiesResponse,
  ProductCatalogItem,
  ProductComparisonMatrix,
  ProductHistoryResponse,
  ProductPositioningResponse,
} from '@/types';
import {
  Activity,
  Layers,
  TrendingUp,
  Target,
  Zap,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Package,
} from 'lucide-react';

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [catalogProducts, setCatalogProducts] = useState<ProductCatalogItem[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [destinationCountry, setDestinationCountry] = useState<string>('US');
  const [reportingCurrency, setReportingCurrency] = useState<string>('USD');
  const [selectedDays, setSelectedDays] = useState<number>(30);

  // Data States
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [matrix, setMatrix] = useState<ProductComparisonMatrix | null>(null);
  const [history, setHistory] = useState<ProductHistoryResponse | null>(null);
  const [positioning, setPositioning] = useState<ProductPositioningResponse | null>(null);
  const [opportunities, setOpportunities] = useState<ExportOpportunitiesResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [unreadAlertsCount, setUnreadAlertsCount] = useState<number>(0);

  // 1. Initial Catalog Synchronization
  useEffect(() => {
    async function initCatalog() {
      try {
        const list = await apiClient.listCatalogProducts();
        setCatalogProducts(list);
        if (list.length > 0) {
          setSelectedProductId((prev) => (prev && list.some((p) => p.id === prev) ? prev : list[0].id));
        }
      } catch (err: any) {
        console.warn('Catalog load warning:', err.message);
      }
    }
    initCatalog();
  }, []);

  // 2. Comprehensive Intelligence Sync
  const loadAllData = useCallback(async () => {
    if (!selectedProductId) return;
    try {
      const [sumRes, matRes, histRes, posRes, oppsRes, notifsRes] = await Promise.allSettled([
        apiClient.getDashboardSummary(),
        apiClient.getComparisonMatrix(selectedProductId, destinationCountry, reportingCurrency),
        apiClient.getProductPriceHistory(selectedProductId, reportingCurrency, selectedDays),
        apiClient.getProductPositioning(selectedProductId, destinationCountry, reportingCurrency),
        apiClient.getExportOpportunities(5.0, reportingCurrency),
        apiClient.listNotifications(true),
      ]);

      if (sumRes.status === 'fulfilled') setSummary(sumRes.value);
      if (matRes.status === 'fulfilled') setMatrix(matRes.value);
      if (histRes.status === 'fulfilled') setHistory(histRes.value);
      if (posRes.status === 'fulfilled') setPositioning(posRes.value);
      if (oppsRes.status === 'fulfilled') setOpportunities(oppsRes.value);
      if (notifsRes.status === 'fulfilled') setUnreadAlertsCount(notifsRes.value.length);
    } catch (err: any) {
      console.warn('Data sync warning:', err.message);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [selectedProductId, destinationCountry, reportingCurrency, selectedDays]);

  useEffect(() => {
    if (selectedProductId) {
      setLoading(true);
      loadAllData();
    }
  }, [selectedProductId, loadAllData]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadAllData();
  };

  const selectedProduct = catalogProducts.find((p) => p.id === selectedProductId) || catalogProducts[0];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Header Navbar */}
      <Navbar
        destinationCountry={destinationCountry}
        setDestinationCountry={setDestinationCountry}
        reportingCurrency={reportingCurrency}
        setReportingCurrency={setReportingCurrency}
        unreadAlertsCount={unreadAlertsCount}
        onOpenNotifications={() => setActiveTab('alerts')}
        onRefreshData={handleRefresh}
        isRefreshing={isRefreshing}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Left Navigation Sidebar */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          selectedProductId={selectedProductId}
          setSelectedProductId={setSelectedProductId}
          unreadAlertsCount={unreadAlertsCount}
          catalogProducts={catalogProducts}
        />

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6">
          {/* Active Product Context Banner */}
          {selectedProduct && (
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 px-4 py-2.5 rounded-xl border border-slate-800/80 bg-slate-900/40 text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <Package className="h-4 w-4 text-cyan-400" />
                <span>Active Canonical Focus:</span>
                <span className="font-bold text-white">{selectedProduct.title}</span>
                <span className="font-mono text-cyan-300">({selectedProduct.sku || selectedProduct.category})</span>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-slate-500 text-[11px]">Quick Switch:</label>
                <select
                  value={selectedProductId}
                  onChange={(e) => setSelectedProductId(e.target.value)}
                  className="rounded-lg border border-slate-700 bg-slate-950 px-2 py-1 text-slate-200 text-xs focus:border-cyan-400 focus:outline-none cursor-pointer"
                >
                  {catalogProducts.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.title} ({p.sku || p.category})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* Executive Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* KPI Cards */}
              <KPICards summary={summary} loading={loading} />

              {/* Grid: Comparison Matrix & Positioning Recommendations */}
              <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
                <div className="xl:col-span-8 space-y-6">
                  <ComparisonMatrixView
                    matrix={matrix}
                    loading={loading}
                    destinationCountry={destinationCountry}
                    reportingCurrency={reportingCurrency}
                  />
                </div>

                <div className="xl:col-span-4 space-y-6">
                  {/* Strategic Action Card */}
                  {positioning && (
                    <div className="rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/40 p-5 space-y-3 shadow-xl">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">
                          Strategic Pricing Advice
                        </span>
                        <Target className="h-4 w-4 text-cyan-400" />
                      </div>
                      <h3 className="text-sm font-bold text-white">{positioning.strategic_recommendation.replace(/_/g, ' ').toUpperCase()}</h3>
                      <p className="text-xs text-slate-300 leading-relaxed">{positioning.recommendation_reasoning}</p>
                      <button
                        onClick={() => setActiveTab('positioning')}
                        className="w-full flex items-center justify-center gap-1.5 rounded-xl bg-indigo-600/30 hover:bg-indigo-600/50 py-2 text-xs font-semibold text-cyan-300 border border-indigo-500/30 transition cursor-pointer"
                      >
                        <span>Explore Full Positioning Matrix</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}

                  {/* Scraper Infrastructure Telemetry */}
                  {summary && (
                    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-3 backdrop-blur-md">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                          Scraping Infrastructure
                        </span>
                        <Activity className="h-4 w-4 text-emerald-400" />
                      </div>

                      <div className="space-y-2 text-xs font-mono">
                        <div className="flex justify-between py-1 border-b border-slate-800">
                          <span className="text-slate-400 font-sans">Total Ingestion Jobs</span>
                          <span className="text-white font-bold">{summary.scraping_health.total_jobs}</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-slate-800">
                          <span className="text-slate-400 font-sans">Extraction Success Rate</span>
                          <span className="text-emerald-400 font-bold">{summary.scraping_health.success_rate_pct}%</span>
                        </div>
                        <div className="flex justify-between py-1 border-b border-slate-800">
                          <span className="text-slate-400 font-sans">Total Records Extracted</span>
                          <span className="text-cyan-400 font-bold">{summary.scraping_health.total_records_extracted}</span>
                        </div>
                      </div>

                      <button
                        onClick={() => setActiveTab('scraping')}
                        className="w-full flex items-center justify-center gap-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 py-2 text-xs font-semibold text-slate-200 transition cursor-pointer"
                      >
                        <span>Launch Scraper Sandbox</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}

                  {/* Platform Recent Activity Stream */}
                  {summary && summary.recent_activities.length > 0 && (
                    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-3 backdrop-blur-md">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                        Recent Activity Stream
                      </span>
                      <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
                        {summary.recent_activities.map((act, i) => (
                          <div key={i} className="p-2 rounded-lg bg-slate-950/80 border border-slate-800/80 text-[11px] space-y-1">
                            <div className="flex items-center justify-between font-semibold text-slate-200">
                              <span>{act.title}</span>
                              <span className="text-[10px] text-slate-500 font-mono">
                                {new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>
                            <p className="text-slate-400 truncate">{act.message}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Landed Cost Matrix Tab */}
          {activeTab === 'comparison' && (
            <ComparisonMatrixView
              matrix={matrix}
              loading={loading}
              destinationCountry={destinationCountry}
              reportingCurrency={reportingCurrency}
            />
          )}

          {/* Historical Trends Tab */}
          {activeTab === 'trends' && (
            <PriceHistoryView
              history={history}
              loading={loading}
              reportingCurrency={reportingCurrency}
              selectedDays={selectedDays}
              setSelectedDays={setSelectedDays}
            />
          )}

          {/* Market Positioning & Arbitrage Tab */}
          {activeTab === 'positioning' && (
            <MarketPositioningView
              positioning={positioning}
              opportunities={opportunities}
              loading={loading}
              reportingCurrency={reportingCurrency}
            />
          )}

          {/* Scraping Hub Tab */}
          {activeTab === 'scraping' && <ScrapingHubView />}

          {/* Landed Cost Simulator Tab */}
          {activeTab === 'simulator' && <LandedCostSimulatorView />}

          {/* Alert Center Tab */}
          {activeTab === 'alerts' && (
            <AlertCenterView
              selectedProductId={selectedProductId}
              onRefreshUnreadCount={loadAllData}
            />
          )}
        </main>
      </div>
    </div>
  );
}
