'use client';

import React from 'react';
import {
  Target,
  Zap,
  TrendingUp,
  Download,
  Award,
  Sparkles,
  ArrowRight,
  TrendingDown,
  CheckCircle,
  Activity,
  Layers,
} from 'lucide-react';
import {
  ExportOpportunitiesResponse,
  ProductPositioningResponse,
} from '@/types';
import { apiClient } from '@/services/api';
import { fmt, fmtPct, num } from '@/utils/format';

interface MarketPositioningViewProps {
  positioning: ProductPositioningResponse | null;
  opportunities: ExportOpportunitiesResponse | null;
  loading: boolean;
  reportingCurrency: string;
}

export const MarketPositioningView: React.FC<MarketPositioningViewProps> = ({
  positioning,
  opportunities,
  loading,
  reportingCurrency,
}) => {
  if (loading || !positioning) {
    return (
      <div className="space-y-4">
        <div className="h-44 animate-pulse rounded-3xl bg-white/[0.03] border border-white/[0.08]" />
        <div className="h-64 animate-pulse rounded-3xl bg-white/[0.03] border border-white/[0.08]" />
      </div>
    );
  }

  const handleDownloadOppsCsv = () => {
    const url = apiClient.getOpportunitiesExportUrl(5.0, reportingCurrency);
    window.open(url, '_blank');
  };

  const getRecommendationBadge = (rec: string) => {
    switch (rec) {
      case 'raise_price_to_maximize_margin':
        return {
          title: 'Raise Price to Maximize Margin',
          color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.25)]',
          icon: TrendingUp,
        };
      case 'maintain_price':
        return {
          title: 'Optimal Market Positioning (Maintain)',
          color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.25)]',
          icon: CheckCircle,
        };
      case 'lower_price_to_compete':
        return {
          title: 'Defend Market Share (Lower Price)',
          color: 'bg-rose-500/20 text-rose-300 border-rose-500/40 shadow-[0_0_15px_rgba(244,63,94,0.25)]',
          icon: TrendingDown,
        };
      default:
        return {
          title: 'Differentiate or Match Price Leader',
          color: 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-[0_0_15px_rgba(245,158,11,0.25)]',
          icon: Sparkles,
        };
    }
  };

  const recBadge = getRecommendationBadge(positioning.strategic_recommendation);
  const RecIcon = recBadge.icon;

  return (
    <div className="space-y-6">
      {/* Strategic AI Recommendation Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/60 via-[#0a0f1d] to-[#040814] p-7 shadow-2xl backdrop-blur-2xl">
        <div className="absolute top-0 left-20 right-20 h-[1px] bg-gradient-to-r from-transparent via-cyan-400/40 to-transparent"></div>

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-5">
          <div className="space-y-2.5 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1 text-xs font-bold border ${recBadge.color}`}>
                <RecIcon className="h-3.5 w-3.5" />
                {recBadge.title}
              </span>
              <span className="rounded-full bg-white/[0.06] border border-white/[0.1] px-2.5 py-0.5 text-xs text-slate-300 uppercase font-mono tracking-wider">
                COMPETITIVENESS: {positioning.market_competitiveness.replace('_', ' ')}
              </span>
            </div>
            <h2 className="text-xl font-black text-white tracking-tight">
              Strategic Market Intelligence: {positioning.product_title}
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed font-normal">
              {positioning.recommendation_reasoning}
            </p>
          </div>

          <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center border-t sm:border-t-0 sm:border-l border-white/[0.1] pt-4 sm:pt-0 sm:pl-7">
            <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400">Positioning Index</span>
            <span className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-indigo-300 to-white font-mono my-0.5">
              {fmt(positioning.positioning_index, 2, '1.00')}x
            </span>
            <span className="text-[10px] text-slate-400">
              Gap vs Median:{' '}
              <span className={`font-mono font-bold ${num(positioning.price_gap_vs_median_pct) <= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {fmtPct(positioning.price_gap_vs_median_pct, 1)}
              </span>
            </span>
          </div>
        </div>
      </div>

      {/* Competitor Median Benchmarking Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 backdrop-blur-xl hover:border-cyan-500/40 transition">
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">Our Landed Cost</span>
          <div className="text-xl font-black text-cyan-300 font-mono mt-1.5">
            {reportingCurrency} {fmt(positioning.our_target_landed_cost, 2, 'N/A')}
          </div>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 backdrop-blur-xl hover:border-indigo-500/40 transition">
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">Marketplace Median</span>
          <div className="text-xl font-black text-slate-200 font-mono mt-1.5">
            {reportingCurrency} {fmt(positioning.competitor_median_landed_cost, 2, 'N/A')}
          </div>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 backdrop-blur-xl hover:border-emerald-500/40 transition">
          <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 block">Market Floor (Lowest)</span>
          <div className="text-xl font-black text-emerald-300 font-mono mt-1.5">
            {reportingCurrency} {fmt(positioning.competitor_min_landed_cost, 2, 'N/A')}
          </div>
        </div>
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 backdrop-blur-xl hover:border-rose-500/40 transition">
          <span className="text-[10px] uppercase font-bold tracking-wider text-rose-400 block">Market Ceiling (Highest)</span>
          <div className="text-xl font-black text-rose-300 font-mono mt-1.5">
            {reportingCurrency} {fmt(positioning.competitor_max_landed_cost, 2, 'N/A')}
          </div>
        </div>
      </div>

      {/* Competitor Ranking Ladder */}
      <div className="overflow-hidden rounded-3xl border border-white/[0.08] bg-gradient-to-b from-white/[0.04] to-transparent backdrop-blur-2xl shadow-xl">
        <div className="px-6 py-4.5 border-b border-white/[0.08] flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Award className="h-4 w-4 text-amber-400" />
            Regional Competitor Ranking Ladder
          </h3>
          <span className="text-xs text-slate-400 font-mono">Ranked by Burdened Landed Cost</span>
        </div>

        <div className="p-4 space-y-2.5">
          {positioning.rankings.map((rank) => (
            <div
              key={rank.listing_id}
              className={`flex items-center justify-between p-3.5 rounded-2xl border transition-all duration-200 ${
                rank.is_cheapest
                  ? 'bg-emerald-500/[0.08] border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.15)]'
                  : 'bg-white/[0.02] border-white/[0.05] hover:bg-white/[0.05] hover:border-white/[0.1]'
              }`}
            >
              <div className="flex items-center gap-3.5">
                <span
                  className={`flex h-7 w-7 items-center justify-center rounded-xl text-xs font-black shadow-sm ${
                    rank.rank === 1
                      ? 'bg-gradient-to-br from-amber-300 to-amber-500 text-slate-950'
                      : rank.rank === 2
                      ? 'bg-gradient-to-br from-slate-200 to-slate-400 text-slate-950'
                      : 'bg-white/[0.08] text-slate-400 border border-white/[0.08]'
                  }`}
                >
                  #{rank.rank}
                </span>
                <div>
                  <span className="font-bold text-white text-xs block">{rank.marketplace_name}</span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    Sticker: {rank.original_currency} {fmt(rank.original_price, 2)} • Tier: {rank.position_tier.toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="text-right">
                <div className="text-sm font-black font-mono text-white">
                  {reportingCurrency} {fmt(rank.landed_cost, 2)}
                </div>
                {rank.price_gap_vs_our_product_pct !== undefined && rank.price_gap_vs_our_product_pct !== null && (
                  <span
                    className={`text-[10px] font-mono font-bold ${
                      num(rank.price_gap_vs_our_product_pct) > 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {fmtPct(rank.price_gap_vs_our_product_pct, 1)} vs our price
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Cross-Border Arbitrage Opportunities */}
      <div className="rounded-3xl border border-white/[0.08] bg-gradient-to-b from-white/[0.04] to-transparent p-6 backdrop-blur-2xl shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
          <div>
            <h3 className="text-base font-extrabold text-white flex items-center gap-2">
              <Zap className="h-4 w-4 text-violet-400" />
              High-Margin Cross-Border Export Arbitrage Corridors
            </h3>
            <p className="text-xs text-slate-400">
              Corridors where purchasing in Source Market and exporting to Target yields high net margin
            </p>
          </div>

          <button
            onClick={handleDownloadOppsCsv}
            className="flex items-center gap-2 rounded-2xl border border-violet-500/30 bg-violet-500/10 px-4 py-2 text-xs font-bold text-violet-300 hover:bg-violet-500/20 transition cursor-pointer shadow-[0_0_15px_rgba(139,92,246,0.15)]"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export Arbitrage CSV</span>
          </button>
        </div>

        {opportunities && opportunities.opportunities.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {opportunities.opportunities.map((opp, idx) => (
              <div
                key={idx}
                className="rounded-2xl border border-violet-500/20 bg-gradient-to-br from-white/[0.03] to-violet-950/20 p-5 space-y-3.5 backdrop-blur-xl hover:border-violet-400/40 transition shadow-lg"
              >
                <div className="flex items-center justify-between">
                  <span className="font-extrabold text-white text-xs truncate max-w-[220px]">{opp.product_title}</span>
                  <span className="rounded-full bg-violet-500/20 px-2.5 py-0.5 text-[10px] font-black text-violet-300 border border-violet-500/40">
                    SCORE: {opp.opportunity_score}/100 ({opp.feasibility_rating.toUpperCase()})
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs bg-black/40 p-3 rounded-xl border border-white/[0.06]">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">SOURCE</span>
                    <span className="font-bold text-slate-200 text-xs">{opp.source_marketplace}</span>
                    <span className="text-[10px] text-slate-400 block font-mono">
                      {opp.source_currency} {fmt(opp.source_price, 2)}
                    </span>
                  </div>
                  <div className="flex flex-col items-center px-2">
                    <span className="text-[9px] text-violet-400 font-mono mb-0.5">TRANSIT</span>
                    <ArrowRight className="h-4 w-4 text-violet-400" />
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">TARGET</span>
                    <span className="font-bold text-slate-200 text-xs">{opp.target_marketplace}</span>
                    <span className="text-[10px] text-slate-400 block font-mono">
                      {opp.target_currency} {fmt(opp.target_market_price, 2)}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1 border-t border-white/[0.08] text-xs">
                  <div>
                    <span className="text-[10px] text-slate-400 block font-medium">Landed Cost in Target</span>
                    <span className="font-mono text-slate-200 font-bold">
                      {opp.reporting_currency} {fmt(opp.landed_cost_in_target, 2)}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 block font-medium">Net Arbitrage Spread</span>
                    <span className="font-mono text-emerald-400 font-black text-sm">
                      {fmtPct(opp.net_margin_pct, 1)} ({opp.reporting_currency} {fmt(opp.net_profit_margin, 2)})
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-10 text-xs text-slate-500 italic">
            No active cross-border arbitrage opportunities exceeding minimum margin threshold.
          </div>
        )}
      </div>
    </div>
  );
};

