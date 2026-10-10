'use client';

import React from 'react';
import {
  Package,
  Store,
  LineChart,
  Bell,
  AlertTriangle,
  Zap,
  TrendingDown,
  Globe2,
} from 'lucide-react';
import { DashboardSummaryResponse } from '@/types';

interface KPICardsProps {
  summary: DashboardSummaryResponse | null;
  loading: boolean;
}

export const KPICards: React.FC<KPICardsProps> = ({ summary, loading }) => {
  if (loading || !summary) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-xl bg-slate-900/60 border border-slate-800" />
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
      gradient: 'from-blue-600/20 to-indigo-600/20 text-indigo-400 border-indigo-500/30',
    },
    {
      title: 'Active Listings',
      value: summary.total_listings,
      subtitle: 'Across 5 Countries',
      icon: Store,
      gradient: 'from-cyan-600/20 to-blue-600/20 text-cyan-400 border-cyan-500/30',
    },
    {
      title: 'Price Points',
      value: summary.total_observations.toLocaleString(),
      subtitle: 'Immutable History',
      icon: LineChart,
      gradient: 'from-emerald-600/20 to-teal-600/20 text-emerald-400 border-emerald-500/30',
    },
    {
      title: 'Active Alerts',
      value: summary.active_alerts_count,
      subtitle: `${summary.unacknowledged_notifications_count} Unacknowledged`,
      icon: Bell,
      gradient: 'from-amber-600/20 to-orange-600/20 text-amber-400 border-amber-500/30',
    },
    {
      title: 'Price Anomalies',
      value: summary.total_anomalies_count,
      subtitle: 'Drops & Spikes >15%',
      icon: AlertTriangle,
      gradient: 'from-rose-600/20 to-red-600/20 text-rose-400 border-rose-500/30',
    },
    {
      title: 'Export Arbitrage',
      value: summary.total_export_opportunities_count,
      subtitle: 'High Margin Deals',
      icon: Zap,
      gradient: 'from-violet-600/20 to-purple-600/20 text-violet-400 border-violet-500/30',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map((card, i) => {
        const Icon = card.icon;
        return (
          <div
            key={i}
            className={`relative overflow-hidden rounded-xl border bg-gradient-to-br p-3.5 backdrop-blur-sm transition hover:scale-[1.02] ${card.gradient}`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">{card.title}</span>
              <Icon className="h-4 w-4 opacity-80" />
            </div>
            <div className="mt-2 text-2xl font-bold tracking-tight text-white">{card.value}</div>
            <p className="mt-1 text-[10px] text-slate-400 font-medium truncate">{card.subtitle}</p>
          </div>
        );
      })}
    </div>
  );
};
