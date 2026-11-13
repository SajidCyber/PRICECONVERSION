'use client';

import {
  LayoutDashboard,
  Layers,
  TrendingUp,
  Target,
  Terminal,
  Sliders,
  BellRing,
  Laptop,
  Headphones,
  BookOpen,
  Package,
  Activity,
  Cpu,
} from 'lucide-react';
import { ProductCatalogItem } from '@/types';

export type TabType =
  | 'overview'
  | 'comparison'
  | 'trends'
  | 'positioning'
  | 'scraping'
  | 'simulator'
  | 'alerts';

interface SidebarProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  selectedProductId: string;
  setSelectedProductId: (id: string) => void;
  unreadAlertsCount: number;
  catalogProducts?: ProductCatalogItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  selectedProductId,
  setSelectedProductId,
  unreadAlertsCount,
  catalogProducts = [],
}) => {
  const navItems = [
    { id: 'overview', label: 'Executive Dashboard', icon: LayoutDashboard },
    { id: 'comparison', label: 'Landed Cost Matrix', icon: Layers },
    { id: 'trends', label: 'Price Trends & Volatility', icon: TrendingUp },
    { id: 'positioning', label: 'Market Positioning & Arbitrage', icon: Target },
    { id: 'simulator', label: 'Landed Cost Simulator', icon: Sliders },
    { id: 'scraping', label: 'Scraping Hub & Ingestion', icon: Terminal },
    { id: 'alerts', label: 'Alerts & Triggers', icon: BellRing, badge: unreadAlertsCount },
  ];

  const getProductIcon = (title: string, category: string) => {
    const lower = `${title} ${category}`.toLowerCase();
    if (lower.includes('headphone') || lower.includes('audio') || lower.includes('earbud')) return Headphones;
    if (lower.includes('book') || lower.includes('literature')) return BookOpen;
    if (lower.includes('laptop') || lower.includes('macbook') || lower.includes('computer')) return Laptop;
    return Package;
  };

  return (
    <aside className="w-68 shrink-0 border-r border-white/[0.08] bg-[#030712]/60 backdrop-blur-2xl p-4 flex flex-col justify-between hidden md:flex">
      <div className="space-y-6">
        {/* Navigation Section */}
        <div>
          <div className="flex items-center justify-between px-3 mb-2.5">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
              CORE PROTOCOLS
            </p>
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
          </div>
          <nav className="space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as TabType)}
                  className={`w-full group relative flex items-center justify-between rounded-xl px-3.5 py-2.5 text-xs font-semibold transition-all duration-200 cursor-pointer ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-500/20 via-indigo-500/15 to-transparent text-white border border-cyan-500/40 shadow-[0_0_20px_rgba(6,182,212,0.15)]'
                      : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-100 border border-transparent'
                  }`}
                >
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 rounded-r-full bg-gradient-to-b from-cyan-400 to-indigo-500 shadow-[0_0_8px_#06b6d4]"></div>
                  )}
                  <div className="flex items-center gap-3">
                    <Icon className={`h-4 w-4 transition-colors ${isActive ? 'text-cyan-400' : 'text-slate-400 group-hover:text-cyan-300'}`} />
                    <span className="tracking-tight">{item.label}</span>
                  </div>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span className="rounded-full bg-rose-500/20 px-2 py-0.5 text-[10px] font-extrabold text-rose-300 border border-rose-500/40 animate-pulse">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tracked Benchmark Products */}
        <div>
          <div className="flex items-center justify-between px-3 mb-2.5">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
              CANONICAL REPOSITORY
            </p>
            <span className="rounded-md bg-white/[0.06] px-1.5 py-0.5 text-[10px] text-cyan-300 font-mono font-bold border border-white/[0.08]">
              {catalogProducts.length}
            </span>
          </div>
          <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
            {catalogProducts.length > 0 ? (
              catalogProducts.map((p) => {
                const Icon = getProductIcon(p.title, p.category);
                const isSelected = selectedProductId === p.id;
                return (
                  <button
                    key={p.id}
                    onClick={() => setSelectedProductId(p.id)}
                    className={`w-full text-left rounded-xl p-2.5 text-xs transition-all duration-200 border cursor-pointer ${
                      isSelected
                        ? 'bg-gradient-to-br from-indigo-950/60 to-slate-900/90 border-cyan-500/50 text-white shadow-lg shadow-cyan-950/30'
                        : 'bg-white/[0.02] border-white/[0.05] text-slate-400 hover:bg-white/[0.05] hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className={`h-3.5 w-3.5 shrink-0 ${isSelected ? 'text-cyan-400' : 'text-slate-500'}`} />
                      <span className="font-semibold truncate text-slate-200 text-[11px]">{p.title}</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                      <span>{p.sku || p.category}</span>
                      {isSelected ? (
                        <span className="flex items-center gap-1 text-cyan-300 font-bold">
                          <span className="h-1.5 w-1.5 rounded-full bg-cyan-400"></span>
                          TRACKING
                        </span>
                      ) : (
                        <span>{p.listings_count || 1} feeds</span>
                      )}
                    </div>
                  </button>
                );
              })
            ) : (
              <div className="p-3 text-center text-[11px] text-slate-500 italic">
                Loading products...
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Cybernetic Telemetry Footer Card */}
      <div className="rounded-2xl border border-white/[0.08] bg-gradient-to-b from-white/[0.04] to-transparent p-3.5 text-[11px] backdrop-blur-xl">
        <div className="flex items-center justify-between font-bold text-slate-200 mb-1.5">
          <div className="flex items-center gap-1.5">
            <Cpu className="h-3.5 w-3.5 text-cyan-400" />
            <span className="text-[11px] tracking-wide">QUANT ENGINE</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping"></span>
            ACTIVE
          </span>
        </div>
        <p className="text-[10px] text-slate-400 leading-relaxed font-mono">
          SSRF Filter: OK • FX Sync: Active • SQLite Persistence
        </p>
      </div>
    </aside>
  );
};

