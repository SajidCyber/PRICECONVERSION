'use client';

import React, { useState } from 'react';
import {
  TrendingUp,
  Download,
  Calendar,
  Activity,
  Zap,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Brush,
} from 'recharts';
import { ProductHistoryResponse } from '@/types';
import { apiClient } from '@/services/api';
import { fmt, fmtPct, num } from '@/utils/format';

interface PriceHistoryViewProps {
  history: ProductHistoryResponse | null;
  loading: boolean;
  reportingCurrency: string;
  selectedDays: number;
  setSelectedDays: (days: number) => void;
}

export const PriceHistoryView: React.FC<PriceHistoryViewProps> = ({
  history,
  loading,
  reportingCurrency,
  selectedDays,
  setSelectedDays,
}) => {
  if (loading || !history) {
    return (
      <div className="space-y-4">
        <div className="h-28 animate-pulse rounded-2xl bg-slate-900 border border-slate-800" />
        <div className="h-80 animate-pulse rounded-2xl bg-slate-900 border border-slate-800" />
      </div>
    );
  }

  const handleExportHistoryCsv = () => {
    const url = apiClient.getHistoryExportUrl(history.product_id, reportingCurrency, selectedDays);
    window.open(url, '_blank');
  };

  const colors = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

  return (
    <div className="space-y-6">
      {/* Top Header & Range Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-cyan-400" />
            <h2 className="text-base font-bold text-white">Historical Price Tracking & Volatility</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Analyzing {history.total_observations} price points across {history.marketplaces_tracked} regional marketplaces
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Day range buttons */}
          <div className="flex items-center rounded-xl bg-slate-950 p-1 border border-slate-800 text-xs">
            {[7, 30, 90, 180, 0].map((d) => (
              <button
                key={d}
                onClick={() => setSelectedDays(d)}
                className={`rounded-lg px-2.5 py-1 font-medium transition cursor-pointer ${
                  selectedDays === d
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {d === 0 ? 'All' : `${d}D`}
              </button>
            ))}
          </div>

          <button
            onClick={handleExportHistoryCsv}
            className="flex items-center gap-1.5 rounded-xl border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition cursor-pointer"
          >
            <Download className="h-3.5 w-3.5 text-cyan-400" />
            <span>Export History</span>
          </button>
        </div>
      </div>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5">
          <span className="text-[10px] uppercase font-semibold text-slate-400">All-Time Low ({reportingCurrency})</span>
          <div className="text-xl font-bold text-emerald-400 font-mono mt-1">
            {reportingCurrency} {fmt(history.overall_min_converted, 2)}
          </div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5">
          <span className="text-[10px] uppercase font-semibold text-slate-400">All-Time High ({reportingCurrency})</span>
          <div className="text-xl font-bold text-rose-400 font-mono mt-1">
            {reportingCurrency} {fmt(history.overall_max_converted, 2)}
          </div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5">
          <span className="text-[10px] uppercase font-semibold text-slate-400">Historical Average</span>
          <div className="text-xl font-bold text-slate-200 font-mono mt-1">
            {reportingCurrency} {fmt(history.overall_avg_converted, 2)}
          </div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5">
          <span className="text-[10px] uppercase font-semibold text-slate-400">Observation Density</span>
          <div className="text-xl font-bold text-cyan-400 font-mono mt-1">
            {num(history.total_observations)} Points
          </div>
        </div>
      </div>

      {/* Multi-Marketplace Time-Series Chart */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
        <h3 className="text-sm font-bold text-white mb-1">Cross-Border Normalized Price Trend Lines</h3>
        <p className="text-xs text-slate-400 mb-4">Converted into normalized reporting currency ({reportingCurrency})</p>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history.timeline_series} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="timestamp"
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 10 }}
                tickFormatter={(val) => {
                  try {
                    const d = new Date(val);
                    return `${d.getMonth() + 1}/${d.getDate()}`;
                  } catch {
                    return val;
                  }
                }}
              />
              <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '0.75rem',
                  color: '#f8fafc',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              {history.listings_history.map((l, i) => (
                <Line
                  key={l.marketplace_id}
                  type="monotone"
                  dataKey={l.marketplace_id}
                  name={l.marketplace_name}
                  stroke={colors[i % colors.length]}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 6 }}
                />
              ))}
              <Brush dataKey="timestamp" height={25} stroke="#334155" fill="#0f172a" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Per-Listing Statistical Detail Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {history.listings_history.map((l) => {
          const s = l.stats;
          const isUp = s.pct_change > 0;
          const isDown = s.pct_change < 0;

          return (
            <div key={l.listing_id} className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-white text-xs">{l.marketplace_name}</h4>
                  <span className="text-[10px] text-slate-500 font-mono">{l.country_id} • {l.currency_code}</span>
                </div>
                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                    s.freshness_status === 'fresh'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : s.freshness_status === 'stale'
                      ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                      : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                  }`}
                >
                  {s.freshness_status.toUpperCase()}
                </span>
              </div>

              <div className="flex items-baseline justify-between border-y border-slate-800/80 py-2">
                <div>
                  <span className="text-[10px] text-slate-400 block">Current Price</span>
                  <span className="text-base font-bold text-white font-mono">
                    {l.currency_code} {fmt(s.current_price, 2)}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 block">Net Change</span>
                  <span
                    className={`text-xs font-bold font-mono flex items-center gap-0.5 justify-end ${
                      isDown ? 'text-emerald-400' : isUp ? 'text-rose-400' : 'text-slate-400'
                    }`}
                  >
                    {isDown ? <ArrowDownRight className="h-3 w-3" /> : isUp ? <ArrowUpRight className="h-3 w-3" /> : null}
                    {fmtPct(s.pct_change, 1)}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center text-[10px]">
                <div className="rounded bg-slate-950/60 p-1.5 border border-slate-800/60">
                  <span className="text-slate-500 block">Min</span>
                  <span className="font-mono text-slate-300 font-semibold">{fmt(s.min_price, 0)}</span>
                </div>
                <div className="rounded bg-slate-950/60 p-1.5 border border-slate-800/60">
                  <span className="text-slate-500 block">Avg</span>
                  <span className="font-mono text-slate-300 font-semibold">{fmt(s.avg_price, 0)}</span>
                </div>
                <div className="rounded bg-slate-950/60 p-1.5 border border-slate-800/60">
                  <span className="text-slate-500 block">Volatility (σ)</span>
                  <span className="font-mono text-cyan-400 font-semibold">{fmt(s.volatility, 1)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
