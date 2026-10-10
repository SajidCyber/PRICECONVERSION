'use client';

import React from 'react';
import {
  Download,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ShieldCheck,
  TrendingUp,
  Tag,
  Ship,
  Scale,
  Percent,
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
        <div className="h-32 animate-pulse rounded-2xl bg-slate-900 border border-slate-800" />
        <div className="h-64 animate-pulse rounded-2xl bg-slate-900 border border-slate-800" />
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
      <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900/90 to-indigo-950/40 p-5 shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-indigo-500/20 px-2 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/30">
                {matrix.product_category || 'Electronics'}
              </span>
              <span className="text-xs text-slate-400 font-mono">{matrix.product_sku}</span>
            </div>
            <h2 className="mt-1 text-xl font-bold text-white tracking-tight">{matrix.product_title}</h2>
            <p className="mt-0.5 text-xs text-slate-400">
              Benchmark Base Price: <span className="font-semibold text-slate-200">${fmt(matrix.target_base_price, 2)} {matrix.base_currency}</span> • Target Destination: <span className="font-semibold text-cyan-400">{matrix.destination_country}</span>
            </p>
          </div>

          {/* KPI Mini Stats */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-2">
              <span className="text-[10px] uppercase font-semibold text-emerald-400 block">Lowest Landed Cost</span>
              <span className="text-base font-bold text-emerald-300">
                {reportingCurrency} {fmt(matrix.lowest_landed_cost, 2)}
              </span>
              <span className="text-[10px] text-emerald-400/80 block truncate">({matrix.cheapest_marketplace || 'N/A'})</span>
            </div>

            <div className="rounded-xl border border-slate-700 bg-slate-800/60 px-3.5 py-2">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Highest Landed Cost</span>
              <span className="text-base font-bold text-slate-200">
                {reportingCurrency} {fmt(matrix.highest_landed_cost, 2)}
              </span>
              <span className="text-[10px] text-slate-400 block">Market Spread: {fmtPct(matrix.landed_cost_spread_pct, 1)}</span>
            </div>

            <button
              onClick={handleDownloadCsv}
              className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-cyan-500/20 hover:opacity-90 transition cursor-pointer"
            >
              <Download className="h-4 w-4" />
              <span>Export CSV</span>
            </button>
          </div>
        </div>
      </div>

      {/* Stacked Landed Cost Composition Chart */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Scale className="h-4 w-4 text-cyan-400" />
              Landed Cost Stack Breakdown by Marketplace
            </h3>
            <p className="text-xs text-slate-400">Total CIF value + Customs Duty + Import VAT/GST + Handling Fees</p>
          </div>
          <span className="text-xs font-mono text-slate-400">Reporting Currency: {reportingCurrency}</span>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
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
              <Bar dataKey="Base Sticker" stackId="a" fill="#6366f1" />
              <Bar dataKey="Freight" stackId="a" fill="#06b6d4" />
              <Bar dataKey="Customs Duty" stackId="a" fill="#f59e0b" />
              <Bar dataKey="Import Tax (VAT/GST)" stackId="a" fill="#ec4899" />
              <Bar dataKey="Handling" stackId="a" fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Landed Cost Multi-Marketplace Breakdown Table */}
      <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-md">
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Tag className="h-4 w-4 text-indigo-400" />
            Detailed Cross-Border Landed Cost Matrix
          </h3>
          <span className="text-xs text-slate-400">{matrix.listings.length} Regional Listings Compared</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Marketplace</th>
                <th className="px-3 py-3">Origin Price</th>
                <th className="px-3 py-3">FX Rate</th>
                <th className="px-3 py-3">Base ({reportingCurrency})</th>
                <th className="px-3 py-3">Freight</th>
                <th className="px-3 py-3">CIF Value</th>
                <th className="px-3 py-3">Customs Duty</th>
                <th className="px-3 py-3">Tax (VAT/GST)</th>
                <th className="px-3 py-3">Handling</th>
                <th className="px-4 py-3 font-bold text-white">Total Landed</th>
                <th className="px-3 py-3">Price Gap</th>
                <th className="px-3 py-3 text-right">Link</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {matrix.listings.map((item) => {
                const b = item.breakdown;
                const isCheapest = item.is_cheapest_landed;
                return (
                  <tr
                    key={item.listing_id}
                    className={`hover:bg-slate-800/40 transition ${
                      isCheapest ? 'bg-emerald-500/5' : ''
                    }`}
                  >
                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white">{item.marketplace_name}</span>
                        <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400">
                          {item.country_id}
                        </span>
                        {isCheapest && (
                          <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3" /> BEST PRICE
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-500 truncate block max-w-xs">{item.listing_title}</span>
                    </td>
                    <td className="px-3 py-3.5 font-mono text-slate-200">
                      {item.original_currency} {fmt(item.original_price, 2)}
                    </td>
                    <td className="px-3 py-3.5 font-mono text-slate-400">{fmt(b.fx_rate, 4)}</td>
                    <td className="px-3 py-3.5 font-mono text-slate-300">{fmt(b.converted_price, 2)}</td>
                    <td className="px-3 py-3.5 font-mono text-slate-300">${fmt(b.freight_fee, 2)}</td>
                    <td className="px-3 py-3.5 font-mono text-slate-300">{fmt(b.cif_value, 2)}</td>
                    <td className="px-3 py-3.5">
                      <div className="font-mono text-slate-200">${fmt(b.customs_duty_amount, 2)}</div>
                      <span className="text-[10px] text-slate-500">
                        {b.is_duty_exempt ? 'De Minimis' : fmtPct(num(b.customs_duty_rate) * 100, 1, false)}
                      </span>
                    </td>
                    <td className="px-3 py-3.5">
                      <div className="font-mono text-slate-200">${fmt(b.import_tax_amount, 2)}</div>
                      <span className="text-[10px] text-slate-500">{fmtPct(num(b.import_tax_rate) * 100, 1, false)}</span>
                    </td>
                    <td className="px-3 py-3.5 font-mono text-slate-300">${fmt(b.handling_fee, 2)}</td>
                    <td className="px-4 py-3.5">
                      <div className={`font-bold font-mono text-sm ${isCheapest ? 'text-emerald-400' : 'text-white'}`}>
                        {reportingCurrency} {fmt(b.total_landed_cost, 2)}
                      </div>
                      <span className="text-[10px] text-slate-500">{fmtPct(b.effective_markup_pct, 1)} landed markup</span>
                    </td>
                    <td className="px-3 py-3.5">
                      {item.price_gap_vs_benchmark_pct !== undefined && item.price_gap_vs_benchmark_pct !== null ? (
                        <span
                          className={`inline-block font-mono text-xs px-2 py-0.5 rounded ${
                            num(item.price_gap_vs_benchmark_pct) <= 0
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : 'bg-rose-500/10 text-rose-400'
                          }`}
                        >
                          {fmtPct(item.price_gap_vs_benchmark_pct, 1)}
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="px-3 py-3.5 text-right">
                      <a
                        href={item.listing_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center justify-center p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
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
