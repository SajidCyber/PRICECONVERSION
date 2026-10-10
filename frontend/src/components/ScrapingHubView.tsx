'use client';

import React, { useState, useEffect } from 'react';
import {
  Terminal,
  Play,
  CheckCircle2,
  AlertOctagon,
  Clock,
  ShieldCheck,
  Globe2,
  RefreshCw,
  Layers,
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
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Terminal className="h-5 w-5 text-cyan-400" />
              <h2 className="text-base font-bold text-white">Live Web Scraping & Ingestion Hub</h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Execute live HTML parsers, mock catalog APIs, and monitor extraction telemetry
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-xl border border-emerald-500/20">
            <ShieldCheck className="h-4 w-4" />
            <span>Pre-flight SSRF & DNS Filter Active</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Job Launcher & Controls */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 backdrop-blur-md">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Play className="h-4 w-4 text-indigo-400" />
            Trigger Scraping Execution
          </h3>

          <div className="space-y-3 text-xs">
            {/* Adapter Selector */}
            <div>
              <label className="text-slate-400 font-medium block mb-1">Target Scraper Adapter</label>
              <select
                value={selectedAdapter}
                onChange={(e) => setSelectedAdapter(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-slate-200 focus:border-cyan-400 focus:outline-none cursor-pointer"
              >
                {adapters.map((a, idx) => {
                  const mId = a.marketplace_id || a.id || `adapter_${idx}`;
                  const mName = a.marketplace_name || a.name || a.adapter_name || mId;
                  const mType = a.is_live_scraper ? 'Live HTML' : 'API Feed';
                  return (
                    <option key={mId} value={mId}>
                      {mName} ({mType})
                    </option>
                  );
                })}
              </select>
            </div>

            {/* Category */}
            <div>
              <label className="text-slate-400 font-medium block mb-1">Category Filter</label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g. travel, laptops, smartphones"
                className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-slate-200 focus:border-cyan-400 focus:outline-none"
              />
            </div>

            {/* Max Pages Slider */}
            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Max Crawl Depth</span>
                <span className="font-mono text-cyan-400 font-bold">{maxPages} Pages</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                value={maxPages}
                onChange={(e) => setMaxPages(Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>

            {/* Rate Limit Delay Slider */}
            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Politeness Rate Delay</span>
                <span className="font-mono text-cyan-400 font-bold">{delaySeconds}s</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="3.0"
                step="0.5"
                value={delaySeconds}
                onChange={(e) => setDelaySeconds(Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>

            {/* Run Button */}
            <button
              onClick={handleRunScraper}
              disabled={isRunning}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 py-3 font-semibold text-white shadow-lg shadow-indigo-500/20 hover:opacity-90 transition disabled:opacity-50 cursor-pointer"
            >
              {isRunning ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Extracting Data...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-white" />
                  <span>Launch Scraper Job</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Columns: Active Telemetry & Logs */}
        <div className="lg:col-span-2 space-y-4">
          {/* Last Job Telemetry */}
          {lastJob && (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4" /> Last Job Completed ({lastJob.id.slice(0, 8)})
                </span>
                <span className="font-mono text-[10px] text-slate-400">{lastJob.created_at}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs font-mono pt-1">
                <div>Discovered: <span className="text-white font-bold">{lastJob.items_discovered}</span></div>
                <div>Extracted: <span className="text-emerald-300 font-bold">{lastJob.items_extracted}</span></div>
                <div>Errors: <span className="text-rose-400 font-bold">{lastJob.error_count}</span></div>
              </div>
            </div>
          )}

          {/* Real-Time Terminal Console */}
          <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4 space-y-2">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="h-2.5 w-2.5 rounded-full bg-rose-500/80" />
                  <div className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
                  <div className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
                </div>
                <span className="text-[11px] font-mono text-slate-400">scraper_telemetry.log</span>
              </div>
              <span className="text-[10px] text-slate-500">Live stdout</span>
            </div>

            <div className="h-64 overflow-y-auto space-y-1.5 font-mono text-[11px] text-slate-300 p-2">
              {recentLogs.length > 0 ? (
                recentLogs.map((log, i) => (
                  <div key={i} className="leading-relaxed text-slate-400">
                    <span className="text-cyan-400">$</span> {log}
                  </div>
                ))
              ) : (
                <div className="text-slate-600 italic">
                  No recent scraping tasks initiated. Click &quot;Launch Scraper Job&quot; to execute real-time extraction.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
