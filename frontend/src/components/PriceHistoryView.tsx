'use client';

import React from 'react';
import {
  TrendingUp,
  Download,
  Calendar,
  Activity,
  Zap,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Radio,
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
        <div className="h-32 animate-pulse rounded-3xl bg-white/[0.03] border border-white/[0.08]" />
        <div className="h-80 animate-pulse rounded-3xl bg-white/[0.03] border border-white/[0.08]" />
      </div>
    );
  }

  const handleExportHistoryCsv = () => {
    const url = apiClient.getHistoryExportUrl(history.product_id, reportingCurrency, selectedDays);
    window.open(url, '_blank');
  };

  const colors = ['#06b6d4', '#6366f1', '#10b981', '#f59e0b', '#ec4899', '#a855f7'];

  return (
    <div className="space-y-6">
      {/* Top Header & Range Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-3xl border border-white/[0.08] bg-gradient-to-r from-white/[0.05] via-[#090e1f] to-[#040814] p-6 backdrop-blur-2xl shadow-xl">
        <div className="flex items-center gap-3.5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 shadow-[0_0_20px_rgba(6,182,212,0.15)]">
            <TrendingUp className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-xl font-black text-white tracking-tight">
              Historical Price Chronology & Volatility (σ)
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Analyzing {history.total_observations} observations across {history.marketplaces_tracked} international markets
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Day range buttons */}
          <div className="flex items-center rounded-2xl bg-black/50 p-1.5 border border-white/[0.08] text-xs">
            {[7, 30, 90, 180, 0].map((d) => (
              <button
                key={d}
                onClick={() => setSelectedDays(d)}
                className={`rounded-xl px-3 py-1.5 font-bold transition-all duration-200 cursor-pointer ${
                  selectedDays === d
                    ? 'bg-gradient-to-r from-cyan-500 to-indigo-600 text-white shadow-[0_0_15px_rgba(6,182,212,0.3)]'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {d === 0 ? 'All Time' : `${d}D`}
              </button>
            ))}
          </div>

          <button
            onClick={handleExportHistoryCsv}
            className="flex items-center gap-2 rounded-2xl border border-white/[0.1] bg-white/[0.04] px-4 py-2.5 text-xs font-bold text-slate-200 hover:text-white hover:border-cyan-500/40 transition cursor-pointer"
          >
            <Download className="h-4 w-4 text-cyan-400" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 backdrop-blur-xl">
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
            All-Time Low ({reportingCurrency})
          </span>
          <div className="text-xl font-black text-emerald-300 font-mono mt-1.5">
            {reportingCurrency} {fmt(history.overall_min_converted, 2)}
          </div>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 backdrop-blur-xl">
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
            All-Time High ({reportingCurrency})
          </span>
          <div className="text-xl font-black text-rose-300 font-mono mt-1.5">
            {reportingCurrency} {fmt(history.overall_max_converted, 2)}
          </div>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 backdrop-blur-xl">
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
            Rolling Arithmetic Mean
          </span>
          <div className="text-xl font-black text-cyan-300 font-mono mt-1.5">
            {reportingCurrency} {fmt(history.overall_avg_converted, 2)}
          </div>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 backdrop-blur-xl">
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
            Ledger Data Points
          </span>
          <div className="text-xl font-black text-indigo-300 font-mono mt-1.5">
            {num(history.total_observations)} Records
          </div>
        </div>
      </div>

      {/* Multi-Marketplace Time-Series Chart */}
      <div className="rounded-3xl border border-white/[0.08] bg-gradient-to-b from-white/[0.04] to-transparent p-6 backdrop-blur-2xl shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-base font-extrabold text-white flex items-center gap-2">
              <Activity className="h-4 w-4 text-cyan-400" />
              Multi-Market Normalized Price Curves
            </h3>
            <p className="text-xs text-slate-400">
              Normalized to baseline currency ({reportingCurrency}) with real-time FX triangulation
            </p>
          </div>
          <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-mono font-bold text-cyan-300 border border-cyan-500/20">
            Sampling: Rolling
          </span>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history.timeline_series} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
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
                  backgroundColor: 'rgba(3, 7, 18, 0.95)',
                  borderColor: 'rgba(255, 255, 255, 0.15)',
                  borderRadius: '1rem',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
                  backdropFilter: 'blur(16px)',
                  color: '#f8fafc',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '12px' }} />
              {history.listings_history.map((l, i) => (
                <Line
                  key={l.marketplace_id}
                  type="monotone"
                  dataKey={l.marketplace_id}
                  name={l.marketplace_name}
                  stroke={colors[i % colors.length]}
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: colors[i % colors.length], strokeWidth: 0 }}
                  activeDot={{ r: 6, stroke: '#ffffff', strokeWidth: 2 }}
                />
              ))}
              <Brush dataKey="timestamp" height={25} stroke="#38bdf8" fill="rgba(15, 23, 42, 0.8)" />
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
            <div
              key={l.listing_id}
              className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5 space-y-4 backdrop-blur-xl hover:border-cyan-500/40 transition"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-extrabold text-white text-xs">{l.marketplace_name}</h4>
                  <span className="text-[10px] text-slate-400 font-mono">{l.country_id} • {l.currency_code}</span>
                </div>
                <span
                  className={`text-[10px] font-black px-2.5 py-0.5 rounded-full border ${
                    s.freshness_status === 'fresh'
                      ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                      : s.freshness_status === 'stale'
                      ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                      : 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                  }`}
                >
                  {s.freshness_status.toUpperCase()}
                </span>
              </div>

              <div className="flex items-baseline justify-between border-y border-white/[0.08] py-3">
                <div>
                  <span className="text-[10px] text-slate-400 font-medium block">Current Spot Price</span>
                  <span className="text-lg font-black text-white font-mono">
                    {l.currency_code} {fmt(s.current_price, 2)}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 font-medium block">Period Delta</span>
                  <span
                    className={`text-xs font-black font-mono flex items-center gap-0.5 justify-end ${
                      isDown ? 'text-emerald-400' : isUp ? 'text-rose-400' : 'text-slate-400'
                    }`}
                  >
                    {isDown ? <ArrowDownRight className="h-3.5 w-3.5" /> : isUp ? <ArrowUpRight className="h-3.5 w-3.5" /> : null}
                    {fmtPct(s.pct_change, 1)}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center text-[10px]">
                <div className="rounded-xl bg-black/40 p-2 border border-white/[0.05]">
                  <span className="text-slate-400 block font-medium">Floor</span>
                  <span className="font-mono text-slate-200 font-bold">{fmt(s.min_price, 0)}</span>
                </div>
                <div className="rounded-xl bg-black/40 p-2 border border-white/[0.05]">
                  <span className="text-slate-400 block font-medium">Mean</span>
                  <span className="font-mono text-slate-200 font-bold">{fmt(s.avg_price, 0)}</span>
                </div>
                <div className="rounded-xl bg-black/40 p-2 border border-white/[0.05]">
                  <span className="text-slate-400 block font-medium">Volatility σ</span>
                  <span className="font-mono text-cyan-300 font-black">{fmt(s.volatility, 1)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

