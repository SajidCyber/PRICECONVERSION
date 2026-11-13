'use client';

import React, { useState, useEffect } from 'react';
import {
  Terminal,
  Play,
  CheckCircle2,
  ShieldCheck,
  RefreshCw,
  Activity,
  Layers,
  Cpu,
} from 'lucide-react';
import { ScraperAdapterInfo, ScrapingJobResponse } from '@/types';
import { apiClient } from '@/services/api';

export const ScrapingHubView: React.FC = () => {
  const [adapters, setAdapters] = useState<ScraperAdapterInfo[]>([]);
  const [selectedAdapter, setSelectedAdapter] = useState<string>('books_to_scrape');
  const [category, setCategory] = useState<string>('travel');
  const [maxPages, setMaxPages] = useState<number>(2);
  const [delaySeconds, setDelaySeconds] = useState<number>(1.0);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [lastJob, setLastJob] = useState<ScrapingJobResponse | null>(null);
  const [recentLogs, setRecentLogs] = useState<string[]>([]);

  useEffect(() => {
    loadAdapters();
  }, []);

  const loadAdapters = async () => {
    try {
      const list = await apiClient.listScraperAdapters();
      setAdapters(list);
    } catch {
      // Fallback adapter list
      setAdapters([
        {
          marketplace_id: 'books_to_scrape',
          marketplace_name: 'Books to Scrape (Live HTML Sandbox)',
          adapter_name: 'books_to_scrape',
          type: 'html_scraper',
          country_id: 'GB',
          base_url: 'https://books.toscrape.com',
          is_live_scraper: true,
          supports_categories: true,
        },
        {
          marketplace_id: 'dummyjson_store',
          marketplace_name: 'DummyJSON Product Catalog Feed',
          adapter_name: 'dummyjson',
          type: 'api_adapter',
          country_id: 'US',
          base_url: 'https://dummyjson.com/products',
          is_live_scraper: false,
          supports_categories: true,
        },
        {
          marketplace_id: 'fakestore',
          marketplace_name: 'FakeStore E-Commerce API',
          adapter_name: 'fakestore',
          type: 'api_adapter',
          country_id: 'US',
          base_url: 'https://fakestoreapi.com/products',
          is_live_scraper: false,
          supports_categories: true,
        },
      ]);
    }
  };

  const handleRunScraper = async () => {
    setIsRunning(true);
    setRecentLogs((prev) => [
      `[${new Date().toLocaleTimeString()}] Initializing ${selectedAdapter} with category='${category}', max_pages=${maxPages}...`,
      ...prev,
    ]);

    try {
      const job = await apiClient.triggerScrapingJob({
        marketplace_id: selectedAdapter,
        category: category || undefined,
        max_pages: maxPages,
        delay_seconds: delaySeconds,
      });

      setLastJob(job);
      setRecentLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] Job ${job.id.slice(0, 8)} status=${job.status}. Extracted ${job.items_extracted} items into observation table.`,
        ...prev,
      ]);
    } catch (err: any) {
      setRecentLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] Error executing scraping job: ${err.message}`,
        ...prev,
      ]);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-3xl border border-white/[0.08] bg-gradient-to-r from-white/[0.05] via-[#091124] to-[#040814] p-6 backdrop-blur-2xl shadow-xl">
        <div className="flex items-center gap-3.5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 shadow-[0_0_20px_rgba(6,182,212,0.15)]">
            <Terminal className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-xl font-black text-white tracking-tight">
              Distributed Web Ingestion & Harvesting Operations
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Execute live HTML parsers, structured market adapters, and inspect real-time extraction telemetry
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-bold text-emerald-300 bg-emerald-500/15 px-3.5 py-2 rounded-2xl border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
          <ShieldCheck className="h-4 w-4" />
          <span>SSRF IP FILTER: ACTIVE</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Job Launcher & Controls (5 cols) */}
        <div className="lg:col-span-5 rounded-3xl border border-white/[0.08] bg-gradient-to-b from-white/[0.04] to-transparent p-6 space-y-5 backdrop-blur-2xl shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
            <h3 className="text-sm font-extrabold text-white flex items-center gap-2">
              <Play className="h-4 w-4 text-cyan-400" />
              Scraper Execution Sandbox
            </h3>
            <span className="text-[10px] text-cyan-300 font-mono font-bold bg-cyan-500/10 px-2 py-0.5 rounded-full border border-cyan-500/20">
              DISPATCH
            </span>
          </div>

          <div className="space-y-4 text-xs">
            {/* Adapter Selector */}
            <div>
              <label className="text-slate-400 font-semibold block mb-1.5">Target Scraper Adapter</label>
              <select
                value={selectedAdapter}
                onChange={(e) => setSelectedAdapter(e.target.value)}
                className="w-full rounded-2xl border border-white/[0.1] bg-black/40 p-3 text-slate-200 font-semibold focus:border-cyan-400 focus:outline-none cursor-pointer transition"
              >
                {adapters.map((a, idx) => {
                  const mId = a.marketplace_id || a.id || `adapter_${idx}`;
                  const mName = a.marketplace_name || a.name || a.adapter_name || mId;
                  const mType = a.is_live_scraper ? 'Live HTML' : 'API Feed';
                  return (
                    <option key={mId} value={mId} className="bg-slate-950 text-white">
                      {mName} ({mType})
                    </option>
                  );
                })}
              </select>
            </div>

            {/* Category */}
            <div>
              <label className="text-slate-400 font-semibold block mb-1.5">Category Target</label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g. travel, laptops, smartphones"
                className="w-full rounded-2xl border border-white/[0.1] bg-black/40 p-3 text-slate-200 font-medium focus:border-cyan-400 focus:outline-none transition"
              />
            </div>

            {/* Max Pages Slider */}
            <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
              <div className="flex justify-between text-slate-300 font-semibold mb-2">
                <span>Max Crawl Depth</span>
                <span className="font-mono text-cyan-300 font-bold bg-cyan-500/10 px-2 py-0.5 rounded-md border border-cyan-500/20">
                  {maxPages} Pages
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                value={maxPages}
                onChange={(e) => setMaxPages(Number(e.target.value))}
                className="w-full cursor-pointer"
              />
            </div>

            {/* Rate Limit Delay Slider */}
            <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
              <div className="flex justify-between text-slate-300 font-semibold mb-2">
                <span>Politeness Rate Delay</span>
                <span className="font-mono text-cyan-300 font-bold bg-cyan-500/10 px-2 py-0.5 rounded-md border border-cyan-500/20">
                  {delaySeconds}s
                </span>
              </div>
              <input
                type="range"
                min="0.5"
                max="3.0"
                step="0.5"
                value={delaySeconds}
                onChange={(e) => setDelaySeconds(Number(e.target.value))}
                className="w-full cursor-pointer"
              />
            </div>

            {/* Run Button */}
            <button
              onClick={handleRunScraper}
              disabled={isRunning}
              className="w-full flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-indigo-700 py-3.5 font-bold text-white shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-[1.01] transition disabled:opacity-50 cursor-pointer"
            >
              {isRunning ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Harvesting Observations...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-white" />
                  <span>Execute Scraper Dispatch</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Columns: Active Telemetry & Logs (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Last Job Telemetry */}
          {lastJob && (
            <div className="rounded-3xl border border-emerald-500/30 bg-gradient-to-b from-emerald-500/10 to-transparent p-5 space-y-3 backdrop-blur-2xl shadow-xl">
              <div className="flex items-center justify-between">
                <span className="font-extrabold text-xs text-emerald-300 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  Last Execution Finished ({lastJob.id.slice(0, 8)})
                </span>
                <span className="font-mono text-[10px] text-slate-400 font-medium">{lastJob.created_at}</span>
              </div>
              <div className="grid grid-cols-3 gap-3 text-xs font-mono pt-1">
                <div className="rounded-xl bg-black/40 p-2.5 border border-white/[0.05]">
                  <span className="text-slate-400 block text-[10px]">Discovered</span>
                  <span className="text-white font-black text-sm">{lastJob.items_discovered}</span>
                </div>
                <div className="rounded-xl bg-black/40 p-2.5 border border-white/[0.05]">
                  <span className="text-slate-400 block text-[10px]">Extracted</span>
                  <span className="text-emerald-300 font-black text-sm">{lastJob.items_extracted}</span>
                </div>
                <div className="rounded-xl bg-black/40 p-2.5 border border-white/[0.05]">
                  <span className="text-slate-400 block text-[10px]">Errors</span>
                  <span className="text-rose-400 font-black text-sm">{lastJob.error_count}</span>
                </div>
              </div>
            </div>
          )}

          {/* Real-Time Terminal Console */}
          <div className="rounded-3xl border border-white/[0.08] bg-black/80 backdrop-blur-2xl p-5 space-y-3 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <div className="flex items-center gap-2.5">
                <div className="flex gap-1.5">
                  <div className="h-2.5 w-2.5 rounded-full bg-rose-500/80" />
                  <div className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
                  <div className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
                </div>
                <span className="text-[11px] font-mono font-bold text-slate-300">scraper_telemetry.log</span>
              </div>
              <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1.5 font-bold">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                STDOUT LIVE
              </span>
            </div>

            <div className="h-72 overflow-y-auto space-y-2 font-mono text-[11px] text-slate-300 p-2">
              {recentLogs.length > 0 ? (
                recentLogs.map((log, i) => (
                  <div key={i} className="leading-relaxed text-slate-300 flex items-start gap-2">
                    <span className="text-cyan-400 font-bold select-none">&gt;</span>
                    <span>{log}</span>
                  </div>
                ))
              ) : (
                <div className="text-slate-600 italic py-16 text-center">
                  Telemetry stream ready. Click &quot;Execute Scraper Dispatch&quot; to begin pipeline extraction.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

