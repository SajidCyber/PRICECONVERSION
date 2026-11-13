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
    <div className="min-h-screen bg-ambient-mesh text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
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
            <div className="relative overflow-hidden flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 px-5 py-3 rounded-2xl border border-white/[0.08] bg-gradient-to-r from-white/[0.05] via-[#090d1c] to-[#040814] text-xs backdrop-blur-xl shadow-lg">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
                  <Package className="h-4 w-4" />
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-slate-400 font-medium">Tracking SKU:</span>
                  <span className="font-extrabold text-white text-sm">{selectedProduct.title}</span>
                  <span className="font-mono text-[10px] text-cyan-300 bg-cyan-500/10 px-2 py-0.5 rounded-full border border-cyan-500/20">
                    {selectedProduct.sku || selectedProduct.category}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2.5">
                <label className="text-slate-400 text-[11px] font-semibold">Switch Focus:</label>
                <select
                  value={selectedProductId}
                  onChange={(e) => setSelectedProductId(e.target.value)}
                  className="rounded-xl border border-white/[0.1] bg-black/60 px-3 py-1.5 text-slate-200 text-xs font-semibold focus:border-cyan-400 focus:outline-none cursor-pointer transition"
                >
                  {catalogProducts.map((p) => (
                    <option key={p.id} value={p.id} className="bg-slate-950 text-white">
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
                    <div className="relative overflow-hidden rounded-3xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/40 via-[#0a0f21] to-[#040814] p-6 space-y-4 shadow-2xl backdrop-blur-2xl">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-black uppercase tracking-widest text-indigo-400">
                          AI QUANT PRICING ADVICE
                        </span>
                        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
                          <Target className="h-3.5 w-3.5" />
                        </div>
                      </div>
                      <h3 className="text-base font-black text-white tracking-tight">
                        {positioning.strategic_recommendation.replace(/_/g, ' ').toUpperCase()}
                      </h3>
                      <p className="text-xs text-slate-300 leading-relaxed font-normal">
                        {positioning.recommendation_reasoning}
                      </p>
                      <button
                        onClick={() => setActiveTab('positioning')}
                        className="w-full flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-500/20 via-indigo-600/30 to-indigo-600/20 hover:from-cyan-500/30 hover:to-indigo-600/40 py-2.5 text-xs font-bold text-cyan-300 border border-cyan-500/30 transition shadow-lg cursor-pointer"
                      >
                        <span>Examine Positioning Radar</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}

                  {/* Scraper Infrastructure Telemetry */}
                  {summary && (
                    <div className="rounded-3xl border border-white/[0.08] bg-gradient-to-b from-white/[0.04] to-transparent p-6 space-y-4 backdrop-blur-2xl shadow-xl">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">
                          HARVESTING INFRASTRUCTURE
                        </span>
                        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                          <Activity className="h-3.5 w-3.5" />
                        </div>
                      </div>

                      <div className="space-y-2.5 text-xs font-mono">
                        <div className="flex justify-between items-center py-1.5 border-b border-white/[0.06]">
                          <span className="text-slate-400 font-sans">Active Pipeline Jobs</span>
                          <span className="text-white font-extrabold">{summary.scraping_health.total_jobs}</span>
                        </div>
                        <div className="flex justify-between items-center py-1.5 border-b border-white/[0.06]">
                          <span className="text-slate-400 font-sans">Ingestion Success Ratio</span>
                          <span className="text-emerald-400 font-black">{summary.scraping_health.success_rate_pct}%</span>
                        </div>
                        <div className="flex justify-between items-center py-1.5 border-b border-white/[0.06]">
                          <span className="text-slate-400 font-sans">Total Records Extracted</span>
                          <span className="text-cyan-300 font-black">{summary.scraping_health.total_records_extracted}</span>
                        </div>
                      </div>

                      <button
                        onClick={() => setActiveTab('scraping')}
                        className="w-full flex items-center justify-center gap-2 rounded-2xl border border-white/[0.1] bg-white/[0.03] hover:bg-white/[0.08] py-2.5 text-xs font-bold text-slate-200 transition cursor-pointer"
                      >
                        <span>Access Scraping Sandbox</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}

                  {/* Platform Recent Activity Stream */}
                  {summary && summary.recent_activities.length > 0 && (
                    <div className="rounded-3xl border border-white/[0.08] bg-gradient-to-b from-white/[0.04] to-transparent p-6 space-y-4 backdrop-blur-2xl shadow-xl">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">
                          AUDIT TRAIL TELEMETRY
                        </span>
                        <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping"></span>
                      </div>
                      <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
                        {summary.recent_activities.map((act, i) => (
                          <div key={i} className="p-3 rounded-2xl bg-black/40 border border-white/[0.05] text-[11px] space-y-1">
                            <div className="flex items-center justify-between font-bold text-slate-200">
                              <span>{act.title}</span>
                              <span className="text-[10px] text-cyan-400 font-mono">
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
