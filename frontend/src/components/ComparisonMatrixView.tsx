'use client';

import React from 'react';
import {
  Download,
  CheckCircle2,
  ExternalLink,
  Scale,
  Sparkles,
  ArrowUpRight,
  TrendingDown,
  Layers,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { ProductComparisonMatrix } from '@/types';
import { apiClient } from '@/services/api';
import { fmt, fmtPct, num } from '@/utils/format';

interface ComparisonMatrixViewProps {
  matrix: ProductComparisonMatrix | null;
  loading: boolean;
  destinationCountry: string;
  reportingCurrency: string;
}

export const ComparisonMatrixView: React.FC<ComparisonMatrixViewProps> = ({
  matrix,
  loading,
  destinationCountry,
  reportingCurrency,
}) => {
  if (loading || !matrix) {
    return (
      <div className="space-y-4">
        <div className="h-36 animate-pulse rounded-3xl bg-white/[0.03] border border-white/[0.08]" />
        <div className="h-72 animate-pulse rounded-3xl bg-white/[0.03] border border-white/[0.08]" />
      </div>
    );
  }

  // Format data for stacked bar chart
  const chartData = matrix.listings.map((item) => {
    const b = item.breakdown;
    return {
      name: item.marketplace_name,
      'Base Sticker': num(b.converted_price),
      'Freight': num(b.freight_fee),
      'Customs Duty': num(b.customs_duty_amount),
      'Import Tax (VAT/GST)': num(b.import_tax_amount),
      'Handling': num(b.handling_fee),
      total: num(b.total_landed_cost),
    };
  });

  const handleDownloadCsv = () => {
    const url = apiClient.getComparisonExportUrl(destinationCountry, reportingCurrency);
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Product Summary Hero Card */}
      <div className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-gradient-to-br from-white/[0.07] via-white/[0.02] to-indigo-950/20 p-6 backdrop-blur-2xl shadow-2xl">
        {/* Specular top border */}
        <div className="absolute top-0 left-16 right-16 h-[1px] bg-gradient-to-r from-transparent via-cyan-400/40 to-transparent"></div>

        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-cyan-500/10 px-3 py-0.5 text-xs font-bold text-cyan-300 border border-cyan-500/30">
                <Sparkles className="h-3 w-3" />
                {matrix.product_category || 'Electronics'}
              </span>
              <span className="text-xs text-slate-400 font-mono tracking-wider bg-white/[0.04] px-2.5 py-0.5 rounded-full border border-white/[0.08]">
                {matrix.product_sku}
              </span>
            </div>
            <h2 className="text-2xl font-extrabold text-white tracking-tight">
              {matrix.product_title}
            </h2>
            <p className="text-xs text-slate-400 flex items-center gap-2">
              <span>Benchmark Base Price:</span>
              <span className="font-bold text-slate-200 bg-white/[0.05] px-2 py-0.5 rounded-md">
                ${fmt(matrix.target_base_price, 2)} {matrix.base_currency}
              </span>
              <span>• Target Corridor:</span>
              <span className="font-bold text-cyan-400">{matrix.destination_country}</span>
            </p>
          </div>

          {/* KPI Mini Stats */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-2xl border border-emerald-500/40 bg-gradient-to-b from-emerald-500/15 to-emerald-500/5 px-4 py-2.5 shadow-[0_0_20px_rgba(16,185,129,0.15)]">
              <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 block">
                LOWEST LANDED COST
              </span>
              <span className="text-lg font-black text-emerald-200">
                {reportingCurrency} {fmt(matrix.lowest_landed_cost, 2)}
              </span>
              <span className="text-[10px] text-emerald-300/80 block font-medium truncate">
                {matrix.cheapest_marketplace || 'Optimal Route'}
              </span>
            </div>

            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 backdrop-blur-md">
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
                MARKET SPREAD
              </span>
              <span className="text-lg font-black text-slate-100">
                {fmtPct(matrix.landed_cost_spread_pct, 1)}
              </span>
              <span className="text-[10px] text-slate-400 block">
                Max: {reportingCurrency} {fmt(matrix.highest_landed_cost, 2)}
              </span>
            </div>

            <button
              onClick={handleDownloadCsv}
              className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-indigo-700 px-5 py-3 text-xs font-bold text-white shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-[1.02] transition cursor-pointer"
            >
              <Download className="h-4 w-4" />
              <span>Export CSV</span>
            </button>
          </div>
        </div>
      </div>

      {/* Stacked Landed Cost Composition Chart */}
      <div className="rounded-3xl border border-white/[0.08] bg-gradient-to-b from-white/[0.04] to-transparent p-6 backdrop-blur-2xl shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-6">
          <div>
            <h3 className="text-base font-extrabold text-white flex items-center gap-2">
              <Scale className="h-4 w-4 text-cyan-400" />
              Multi-Marketplace Landed Cost Composition
            </h3>
            <p className="text-xs text-slate-400">
              Stack decomposition: Sticker Price + Freight + Customs Duty + Import VAT/GST + Handling Surcharge
            </p>
          </div>
          <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-mono font-bold text-cyan-300 border border-cyan-500/20">
            Valuation: {reportingCurrency}
          </span>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
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
              <Bar dataKey="Base Sticker" stackId="a" fill="#6366f1" radius={[0, 0, 0, 0]} />
              <Bar dataKey="Freight" stackId="a" fill="#06b6d4" radius={[0, 0, 0, 0]} />
              <Bar dataKey="Customs Duty" stackId="a" fill="#f59e0b" radius={[0, 0, 0, 0]} />
              <Bar dataKey="Import Tax (VAT/GST)" stackId="a" fill="#ec4899" radius={[0, 0, 0, 0]} />
              <Bar dataKey="Handling" stackId="a" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Landed Cost Multi-Marketplace Breakdown Table */}
      <div className="overflow-hidden rounded-3xl border border-white/[0.08] bg-gradient-to-b from-white/[0.04] to-transparent backdrop-blur-2xl shadow-xl">
        <div className="px-6 py-4.5 border-b border-white/[0.08] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">
              Granular Landed Cost Matrix
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {matrix.listings.length} Corridors Active
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-white/[0.02] text-[10px] uppercase tracking-widest text-slate-400 border-b border-white/[0.08]">
              <tr>
                <th className="px-5 py-3.5">Marketplace</th>
                <th className="px-3.5 py-3.5">Origin Price</th>
                <th className="px-3 py-3.5">FX Rate</th>
                <th className="px-3.5 py-3.5">Base ({reportingCurrency})</th>
                <th className="px-3 py-3.5">Freight</th>
                <th className="px-3 py-3.5">CIF Value</th>
                <th className="px-3.5 py-3.5">Duty</th>
                <th className="px-3.5 py-3.5">VAT/GST</th>
                <th className="px-3 py-3.5">Handling</th>
                <th className="px-5 py-3.5 font-bold text-white">Total Landed</th>
                <th className="px-3.5 py-3.5">Price Gap</th>
                <th className="px-4 py-3.5 text-right">View</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.05] font-medium">
              {matrix.listings.map((item) => {
                const b = item.breakdown;
                const isCheapest = item.is_cheapest_landed;
                return (
                  <tr
                    key={item.listing_id}
                    className={`hover:bg-white/[0.04] transition-colors duration-150 ${
                      isCheapest ? 'bg-emerald-500/[0.06]' : ''
                    }`}
                  >
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white">{item.marketplace_name}</span>
                        <span className="rounded-md bg-white/[0.06] px-1.5 py-0.5 text-[10px] text-slate-300 font-mono">
                          {item.country_id}
                        </span>
                        {isCheapest && (
                          <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-extrabold text-emerald-300 border border-emerald-500/40 flex items-center gap-1 shadow-[0_0_10px_rgba(16,185,129,0.3)]">
                            <CheckCircle2 className="h-3 w-3" /> BEST DEAL
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 truncate block max-w-xs mt-0.5 font-normal">
                        {item.listing_title}
                      </span>
                    </td>
                    <td className="px-3.5 py-4 font-mono text-slate-200">
                      {item.original_currency} {fmt(item.original_price, 2)}
                    </td>
                    <td className="px-3 py-4 font-mono text-slate-400">{fmt(b.fx_rate, 4)}</td>
                    <td className="px-3.5 py-4 font-mono text-slate-200">{fmt(b.converted_price, 2)}</td>
                    <td className="px-3 py-4 font-mono text-slate-300">${fmt(b.freight_fee, 2)}</td>
                    <td className="px-3 py-4 font-mono text-slate-300">${fmt(b.cif_value, 2)}</td>
                    <td className="px-3.5 py-4">
                      <div className="font-mono text-slate-200">${fmt(b.customs_duty_amount, 2)}</div>
                      <span className="text-[10px] text-slate-400">
                        {b.is_duty_exempt ? 'Exempt' : fmtPct(num(b.customs_duty_rate) * 100, 1, false)}
                      </span>
                    </td>
                    <td className="px-3.5 py-4">
                      <div className="font-mono text-slate-200">${fmt(b.import_tax_amount, 2)}</div>
                      <span className="text-[10px] text-slate-400">{fmtPct(num(b.import_tax_rate) * 100, 1, false)}</span>
                    </td>
                    <td className="px-3 py-4 font-mono text-slate-300">${fmt(b.handling_fee, 2)}</td>
                    <td className="px-5 py-4">
                      <div className={`font-black font-mono text-sm ${isCheapest ? 'text-emerald-400' : 'text-white'}`}>
                        {reportingCurrency} {fmt(b.total_landed_cost, 2)}
                      </div>
                      <span className="text-[10px] text-slate-400">{fmtPct(b.effective_markup_pct, 1)} markup</span>
                    </td>
                    <td className="px-3.5 py-4">
                      {item.price_gap_vs_benchmark_pct !== undefined && item.price_gap_vs_benchmark_pct !== null ? (
                        <span
                          className={`inline-block font-mono text-xs px-2 py-0.5 rounded-md font-bold ${
                            num(item.price_gap_vs_benchmark_pct) <= 0
                              ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                              : 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                          }`}
                        >
                          {fmtPct(item.price_gap_vs_benchmark_pct, 1)}
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="px-4 py-4 text-right">
                      <a
                        href={item.listing_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center justify-center p-2 rounded-xl text-slate-400 hover:text-cyan-300 hover:bg-white/[0.08] transition"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

