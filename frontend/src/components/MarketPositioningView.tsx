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
  ShieldAlert,
  Percent,
  TrendingDown,
  CheckCircle,
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
        <div className="h-44 animate-pulse rounded-2xl bg-slate-900 border border-slate-800" />
        <div className="h-64 animate-pulse rounded-2xl bg-slate-900 border border-slate-800" />
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
          color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
          icon: TrendingUp,
        };
      case 'maintain_price':
        return {
          title: 'Maintain Current Price (Optimal Positioning)',
          color: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
          icon: CheckCircle,
        };
      case 'lower_price_to_compete':
        return {
          title: 'Lower Price to Defend Market Share',
          color: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
          icon: TrendingDown,
        };
      default:
        return {
          title: 'Differentiate or Match Price Leader',
          color: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
          icon: Sparkles,
        };
    }
  };

  const recBadge = getRecommendationBadge(positioning.strategic_recommendation);
  const RecIcon = recBadge.icon;

  return (
    <div className="space-y-6">
      {/* Strategic AI Recommendation Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/60 via-slate-900 to-slate-900 p-6 shadow-2xl backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-2 max-w-3xl">
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold border ${recBadge.color}`}>
                <RecIcon className="h-3.5 w-3.5" />
                {recBadge.title}
              </span>
              <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-400 uppercase font-semibold">
                Status: {positioning.market_competitiveness.replace('_', ' ')}
              </span>
            </div>
            <h2 className="text-lg font-bold text-white tracking-tight">
              Strategic Positioning for {positioning.product_title}
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              {positioning.recommendation_reasoning}
            </p>
          </div>

          <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center border-t sm:border-t-0 sm:border-l border-slate-800 pt-3 sm:pt-0 sm:pl-6">
            <span className="text-[10px] uppercase font-semibold text-slate-400">Positioning Index</span>
            <span className="text-2xl font-black text-cyan-400 font-mono">
              {fmt(positioning.positioning_index, 2, '1.00')}x
            </span>
            <span className="text-[10px] text-slate-400">
              Gap vs Median: <span className={num(positioning.price_gap_vs_median_pct) <= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                {fmtPct(positioning.price_gap_vs_median_pct, 1)}
              </span>
            </span>
          </div>
        </div>
      </div>

      {/* Competitor Median Benchmarking Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5">
          <span className="text-[10px] uppercase font-semibold text-slate-400">Our Landed Cost</span>
          <div className="text-lg font-bold text-cyan-400 font-mono mt-1">
            {reportingCurrency} {fmt(positioning.our_target_landed_cost, 2, 'N/A')}
          </div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5">
          <span className="text-[10px] uppercase font-semibold text-slate-400">Competitor Median</span>
          <div className="text-lg font-bold text-slate-200 font-mono mt-1">
            {reportingCurrency} {fmt(positioning.competitor_median_landed_cost, 2, 'N/A')}
          </div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5">
          <span className="text-[10px] uppercase font-semibold text-slate-400">Market Floor (Lowest)</span>
          <div className="text-lg font-bold text-emerald-400 font-mono mt-1">
            {reportingCurrency} {fmt(positioning.competitor_min_landed_cost, 2, 'N/A')}
          </div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5">
          <span className="text-[10px] uppercase font-semibold text-slate-400">Market Ceiling (Highest)</span>
          <div className="text-lg font-bold text-rose-400 font-mono mt-1">
            {reportingCurrency} {fmt(positioning.competitor_max_landed_cost, 2, 'N/A')}
          </div>
        </div>
      </div>

      {/* Competitor Ranking Ladder */}
      <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-md">
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Award className="h-4 w-4 text-amber-400" />
            Marketplace Competitor Ranking Ladder
          </h3>
          <span className="text-xs text-slate-400">Ordered by Total Landed Cost</span>
        </div>

        <div className="p-4 space-y-2">
          {positioning.rankings.map((rank) => (
            <div
              key={rank.listing_id}
              className={`flex items-center justify-between p-3 rounded-xl border transition ${
                rank.is_cheapest
                  ? 'bg-emerald-500/10 border-emerald-500/40'
                  : 'bg-slate-950/60 border-slate-800/80 hover:bg-slate-900/80'
              }`}
            >
              <div className="flex items-center gap-3">
                <span
                  className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                    rank.rank === 1
                      ? 'bg-amber-400 text-slate-950 font-black'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  #{rank.rank}
                </span>
                <div>
                  <span className="font-bold text-white text-xs block">{rank.marketplace_name}</span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    Sticker: {rank.original_currency} {fmt(rank.original_price, 2)} • Tier: {rank.position_tier.toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="text-right">
                <div className="text-sm font-bold font-mono text-white">
                  {reportingCurrency} {fmt(rank.landed_cost, 2)}
                </div>
                {rank.price_gap_vs_our_product_pct !== undefined && rank.price_gap_vs_our_product_pct !== null && (
                  <span
                    className={`text-[10px] font-mono ${
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
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Zap className="h-4 w-4 text-violet-400" />
              High-Margin Cross-Border Export Arbitrage Opportunities
            </h3>
            <p className="text-xs text-slate-400">
              Markets where importing from Source yields high gross profit margin in Destination
            </p>
          </div>

          <button
            onClick={handleDownloadOppsCsv}
            className="flex items-center gap-1.5 rounded-xl border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition cursor-pointer"
          >
            <Download className="h-3.5 w-3.5 text-violet-400" />
            <span>Export Arbitrage CSV</span>
          </button>
        </div>

        {opportunities && opportunities.opportunities.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {opportunities.opportunities.map((opp, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-violet-500/20 bg-gradient-to-br from-slate-950 via-slate-900 to-violet-950/20 p-4 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-xs truncate max-w-[200px]">{opp.product_title}</span>
                  <span className="rounded-full bg-violet-500/20 px-2 py-0.5 text-[10px] font-bold text-violet-300 border border-violet-500/30">
                    SCORE: {opp.opportunity_score}/100 ({opp.feasibility_rating.toUpperCase()})
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs bg-slate-950/80 p-2.5 rounded-lg border border-slate-800">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">Source Market</span>
                    <span className="font-semibold text-slate-200">{opp.source_marketplace}</span>
                    <span className="text-[10px] text-slate-400 block font-mono">
                      {opp.source_currency} {fmt(opp.source_price, 2)}
                    </span>
                  </div>
                  <ArrowRight className="h-4 w-4 text-violet-400 shrink-0" />
                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 uppercase block">Target Market</span>
                    <span className="font-semibold text-slate-200">{opp.target_marketplace}</span>
                    <span className="text-[10px] text-slate-400 block font-mono">
                      {opp.target_currency} {fmt(opp.target_market_price, 2)}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1 border-t border-slate-800 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-400 block">Landed Cost in Target</span>
                    <span className="font-mono text-slate-300 font-semibold">
                      {opp.reporting_currency} {fmt(opp.landed_cost_in_target, 2)}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 block">Net Profit Margin</span>
                    <span className="font-mono text-emerald-400 font-bold text-sm">
                      {fmtPct(opp.net_margin_pct, 1)} ({opp.reporting_currency} {fmt(opp.net_profit_margin, 2)})
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-xs text-slate-500">
            No active cross-border arbitrage opportunities exceeding minimum margin threshold.
          </div>
        )}
      </div>
    </div>
  );
};
