'use client';

import React from 'react';
import {
  Globe,
  Bell,
  Download,
  Activity,
  ShieldCheck,
  RefreshCw,
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
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand & Logo */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20">
            <div className="flex h-full w-full items-center justify-center rounded-[10px] bg-slate-950">
              <Globe className="h-5 w-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-white">
                GLOBAL<span className="text-cyan-400">PRICE</span>.AI
              </span>
              <span className="rounded-full bg-indigo-500/10 px-2 py-0.5 text-[10px] font-semibold text-indigo-400 border border-indigo-500/20">
                PRO V2.0
              </span>
            </div>
            <p className="text-xs text-slate-400">Cross-Border Pricing Intelligence & Arbitrage</p>
          </div>
        </div>

        {/* Global Controls & Actions */}
        <div className="flex items-center gap-3">
          {/* Live Engine Status */}
          <div className="hidden md:flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-3 py-1.5 text-xs text-emerald-400">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
            </span>
            <span>Live FX & Scrapers Active</span>
          </div>

          {/* Destination Target Market Selector */}
          <div className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/90 px-2.5 py-1.5 text-xs">
            <span className="text-slate-400">Dest:</span>
            <select
              value={destinationCountry}
              onChange={(e) => setDestinationCountry(e.target.value)}
              className="bg-transparent font-medium text-white focus:outline-none cursor-pointer"
            >
              <option value="US" className="bg-slate-900 text-white">🇺🇸 US (United States)</option>
              <option value="GB" className="bg-slate-900 text-white">🇬🇧 GB (United Kingdom)</option>
              <option value="DE" className="bg-slate-900 text-white">🇩🇪 DE (Germany / EU)</option>
              <option value="IN" className="bg-slate-900 text-white">🇮🇳 IN (India)</option>
              <option value="JP" className="bg-slate-900 text-white">🇯🇵 JP (Japan)</option>
            </select>
          </div>

          {/* Reporting Currency Selector */}
          <div className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/90 px-2.5 py-1.5 text-xs">
            <span className="text-slate-400">Currency:</span>
            <select
              value={reportingCurrency}
              onChange={(e) => setReportingCurrency(e.target.value)}
              className="bg-transparent font-medium text-white focus:outline-none cursor-pointer"
            >
              <option value="USD" className="bg-slate-900 text-white">USD ($)</option>
              <option value="EUR" className="bg-slate-900 text-white">EUR (€)</option>
              <option value="GBP" className="bg-slate-900 text-white">GBP (£)</option>
              <option value="INR" className="bg-slate-900 text-white">INR (₹)</option>
              <option value="JPY" className="bg-slate-900 text-white">JPY (¥)</option>
            </select>
          </div>

          {/* Refresh Action */}
          <button
            onClick={onRefreshData}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition disabled:opacity-50"
            title="Refresh All Engine Data"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
            <span className="hidden sm:inline">Sync</span>
          </button>

          {/* Notification Inbox Button */}
          <button
            onClick={onOpenNotifications}
            className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800 hover:text-white transition"
            title="Active Alert Notifications"
          >
            <Bell className="h-4 w-4" />
            {unreadAlertsCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white shadow-lg shadow-rose-500/40">
                {unreadAlertsCount > 9 ? '9+' : unreadAlertsCount}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
