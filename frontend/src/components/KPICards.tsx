'use client';

import React from 'react';
import {
  Package,
  Store,
  LineChart,
  Bell,
  AlertTriangle,
  Zap,
} from 'lucide-react';
import { DashboardSummaryResponse } from '@/types';

interface KPICardsProps {
  summary: DashboardSummaryResponse | null;
  loading: boolean;
}

export const KPICards: React.FC<KPICardsProps> = ({ summary, loading }) => {
  if (loading || !summary) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-28 animate-pulse rounded-2xl bg-white/[0.03] border border-white/[0.06]" />
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: 'Tracked Products',
      value: summary.total_products,
      subtitle: `${summary.total_marketplaces} Marketplaces`,
      icon: Package,
      aura: 'from-blue-500/20 to-indigo-500/0',
      borderGlow: 'hover:border-indigo-400/50 hover:shadow-[0_0_25px_rgba(99,102,241,0.2)]',
      iconBg: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
      valueColor: 'from-white via-slate-100 to-indigo-300',
    },
    {
      title: 'Active Listings',
      value: summary.total_listings,
      subtitle: 'Across 5 Countries',
      icon: Store,
      aura: 'from-cyan-500/20 to-blue-500/0',
      borderGlow: 'hover:border-cyan-400/50 hover:shadow-[0_0_25px_rgba(6,182,212,0.2)]',
      iconBg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
      valueColor: 'from-white via-slate-100 to-cyan-300',
    },
    {
      title: 'Price Points',
      value: summary.total_observations.toLocaleString(),
      subtitle: 'Immutable Ledger',
      icon: LineChart,
      aura: 'from-emerald-500/20 to-teal-500/0',
      borderGlow: 'hover:border-emerald-400/50 hover:shadow-[0_0_25px_rgba(16,185,129,0.2)]',
      iconBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      valueColor: 'from-white via-slate-100 to-emerald-300',
    },
    {
      title: 'Active Alerts',
      value: summary.active_alerts_count,
      subtitle: `${summary.unacknowledged_notifications_count} Pending`,
      icon: Bell,
      aura: 'from-amber-500/20 to-orange-500/0',
      borderGlow: 'hover:border-amber-400/50 hover:shadow-[0_0_25px_rgba(245,158,11,0.2)]',
      iconBg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      valueColor: 'from-white via-slate-100 to-amber-300',
    },
    {
      title: 'Price Anomalies',
      value: summary.total_anomalies_count,
      subtitle: 'Fluctuations >15%',
      icon: AlertTriangle,
      aura: 'from-rose-500/20 to-pink-500/0',
      borderGlow: 'hover:border-rose-400/50 hover:shadow-[0_0_25px_rgba(244,63,94,0.2)]',
      iconBg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      valueColor: 'from-white via-slate-100 to-rose-300',
    },
    {
      title: 'Export Arbitrage',
      value: summary.total_export_opportunities_count,
      subtitle: 'Profitable Corridors',
      icon: Zap,
      aura: 'from-violet-500/20 to-purple-500/0',
      borderGlow: 'hover:border-violet-400/50 hover:shadow-[0_0_25px_rgba(139,92,246,0.2)]',
      iconBg: 'bg-violet-500/10 text-violet-400 border-violet-500/30',
      valueColor: 'from-white via-slate-100 to-violet-300',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
      {cards.map((card, i) => {
        const Icon = card.icon;
        return (
          <div
            key={i}
            className={`group relative overflow-hidden rounded-2xl border border-white/[0.08] bg-gradient-to-b from-white/[0.05] to-white/[0.01] p-4 backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 cursor-pointer ${card.borderGlow}`}
          >
            {/* Top Specular Line */}
            <div className="absolute top-0 left-10 right-10 h-[1px] bg-gradient-to-r from-transparent via-white/30 to-transparent"></div>
            
            {/* Ambient Background Aura */}
            <div className={`absolute -right-6 -bottom-6 h-24 w-24 rounded-full bg-gradient-to-br ${card.aura} blur-xl group-hover:scale-150 transition-transform duration-500 pointer-events-none`}></div>

            <div className="flex items-center justify-between mb-3">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 truncate mr-1">
                {card.title}
              </span>
              <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border p-1 shadow-sm transition-transform duration-300 group-hover:rotate-6 ${card.iconBg}`}>
                <Icon className="h-3.5 w-3.5" />
              </div>
            </div>

            <div className={`text-2xl font-black tracking-tight bg-gradient-to-r ${card.valueColor} bg-clip-text text-transparent`}>
              {card.value}
            </div>

            <p className="mt-1 text-[10px] font-medium text-slate-400/90 truncate">
              {card.subtitle}
            </p>
          </div>
        );
      })}
    </div>
  );
};

