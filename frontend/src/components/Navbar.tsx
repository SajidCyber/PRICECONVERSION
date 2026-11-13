'use client';

import React from 'react';
import {
  Globe,
  Bell,
  RefreshCw,
  Sparkles,
  Zap,
} from 'lucide-react';

interface NavbarProps {
  destinationCountry: string;
  setDestinationCountry: (c: string) => void;
  reportingCurrency: string;
  setReportingCurrency: (c: string) => void;
  unreadAlertsCount: number;
  onOpenNotifications: () => void;
  onRefreshData: () => void;
  isRefreshing: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  destinationCountry,
  setDestinationCountry,
  reportingCurrency,
  setReportingCurrency,
  unreadAlertsCount,
  onOpenNotifications,
  onRefreshData,
  isRefreshing,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/[0.08] bg-[#030712]/75 backdrop-blur-2xl specular-border">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand & Logo */}
        <div className="flex items-center gap-3.5">
          <div className="relative group cursor-pointer">
            <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-cyan-500 via-indigo-500 to-fuchsia-500 opacity-60 blur-md group-hover:opacity-100 transition duration-500"></div>
            <div className="relative flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-b from-slate-900 to-black border border-white/20 p-2 shadow-inner">
              <Globe className="h-6 w-6 text-cyan-400 group-hover:rotate-12 transition-transform duration-500" />
              <span className="absolute top-1 right-1 flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
              </span>
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-cyan-400 bg-clip-text text-transparent">
                PRICE<span className="text-cyan-400">GLOBE</span>
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-cyan-500/10 to-indigo-500/10 px-2.5 py-0.5 text-[10px] font-semibold text-cyan-300 border border-cyan-500/30 shadow-[0_0_12px_rgba(6,182,212,0.15)]">
                <Sparkles className="h-2.5 w-2.5 text-cyan-400" />
                QUANT V2.5
              </span>
            </div>
            <p className="text-[11px] font-medium text-slate-400 tracking-wide flex items-center gap-1.5">
              <span>Cross-Border Landed Cost Intelligence</span>
              <span className="text-slate-600">•</span>
              <span className="text-emerald-400 font-mono text-[10px]">LIVE FEED</span>
            </p>
          </div>
        </div>

        {/* Global Controls & Actions */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          {/* Live Engine Status Pill */}
          <div className="hidden lg:flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/[0.07] px-3.5 py-1.5 text-xs text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
            </span>
            <span className="font-semibold text-[11px] tracking-wide">FX & SCRAPERS SYNCED</span>
          </div>

          {/* Destination Target Market Selector */}
          <div className="flex items-center gap-1.5 rounded-xl border border-white/[0.1] bg-white/[0.04] px-3 py-1.5 text-xs backdrop-blur-md hover:border-cyan-500/40 transition">
            <span className="text-slate-400 text-[11px] font-medium">Dest:</span>
            <select
              value={destinationCountry}
              onChange={(e) => setDestinationCountry(e.target.value)}
              className="bg-transparent font-semibold text-white focus:outline-none cursor-pointer text-xs"
            >
              <option value="US" className="bg-slate-950 text-white">🇺🇸 United States (US)</option>
              <option value="GB" className="bg-slate-950 text-white">🇬🇧 United Kingdom (GB)</option>
              <option value="DE" className="bg-slate-950 text-white">🇩🇪 Germany / EU (DE)</option>
              <option value="IN" className="bg-slate-950 text-white">🇮🇳 India (IN)</option>
              <option value="JP" className="bg-slate-950 text-white">🇯🇵 Japan (JP)</option>
            </select>
          </div>

          {/* Reporting Currency Selector */}
          <div className="flex items-center gap-1.5 rounded-xl border border-white/[0.1] bg-white/[0.04] px-3 py-1.5 text-xs backdrop-blur-md hover:border-cyan-500/40 transition">
            <span className="text-slate-400 text-[11px] font-medium">Currency:</span>
            <select
              value={reportingCurrency}
              onChange={(e) => setReportingCurrency(e.target.value)}
              className="bg-transparent font-semibold text-cyan-300 focus:outline-none cursor-pointer text-xs"
            >
              <option value="USD" className="bg-slate-950 text-white">USD ($)</option>
              <option value="EUR" className="bg-slate-950 text-white">EUR (€)</option>
              <option value="GBP" className="bg-slate-950 text-white">GBP (£)</option>
              <option value="INR" className="bg-slate-950 text-white">INR (₹)</option>
              <option value="JPY" className="bg-slate-950 text-white">JPY (¥)</option>
            </select>
          </div>

          {/* Refresh Action */}
          <button
            onClick={onRefreshData}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 rounded-xl border border-white/[0.1] bg-gradient-to-r from-cyan-500/10 to-indigo-500/10 px-3.5 py-1.5 text-xs font-semibold text-cyan-300 hover:from-cyan-500/20 hover:to-indigo-500/20 hover:border-cyan-400/40 transition cursor-pointer disabled:opacity-50 shadow-[0_0_15px_rgba(6,182,212,0.1)]"
            title="Refresh All Engine Data"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
            <span className="hidden sm:inline">Sync</span>
          </button>

          {/* Notification Inbox Button */}
          <button
            onClick={onOpenNotifications}
            className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-white/[0.1] bg-white/[0.04] text-slate-300 hover:text-white hover:border-cyan-500/40 transition cursor-pointer"
            title="Active Alert Notifications"
          >
            <Bell className="h-4 w-4" />
            {unreadAlertsCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-extrabold text-white shadow-lg shadow-rose-500/50 animate-pulse">
                {unreadAlertsCount > 9 ? '9+' : unreadAlertsCount}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};

