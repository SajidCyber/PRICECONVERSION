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
    { id: 'trends', label: 'Price History & Volatility', icon: TrendingUp },
    { id: 'positioning', label: 'Positioning & Arbitrage', icon: Target },
    { id: 'scraping', label: 'Scraping Operations', icon: Terminal },
    { id: 'simulator', label: 'Tariff Simulator', icon: Sliders },
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
    <aside className="w-64 shrink-0 border-r border-slate-800/80 bg-slate-950/40 p-4 flex flex-col justify-between hidden md:flex">
      <div className="space-y-6">
        {/* Navigation Section */}
        <div>
          <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2">
            Intelligence Modules
          </p>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as TabType)}
                  className={`w-full flex items-center justify-between rounded-lg px-3 py-2.5 text-xs font-medium transition ${
                    isActive
                      ? 'bg-gradient-to-r from-indigo-600/20 to-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                      : 'text-slate-400 hover:bg-slate-900/80 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span className="rounded-full bg-rose-500/20 px-1.5 py-0.5 text-[10px] font-bold text-rose-400 border border-rose-500/30">
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
          <div className="flex items-center justify-between px-3 mb-2">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Tracked Catalog
            </p>
            <span className="text-[10px] text-cyan-400 font-mono font-bold">
              {catalogProducts.length} Items
            </span>
          </div>
          <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
            {catalogProducts.length > 0 ? (
              catalogProducts.map((p) => {
                const Icon = getProductIcon(p.title, p.category);
                const isSelected = selectedProductId === p.id;
                return (
                  <button
                    key={p.id}
                    onClick={() => setSelectedProductId(p.id)}
                    className={`w-full text-left rounded-lg p-2.5 text-xs transition border cursor-pointer ${
                      isSelected
                        ? 'bg-slate-900 border-indigo-500/50 text-white shadow-md shadow-indigo-950/40'
                        : 'bg-slate-950/60 border-slate-800/80 text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className={`h-3.5 w-3.5 shrink-0 ${isSelected ? 'text-indigo-400' : 'text-slate-500'}`} />
                      <span className="font-medium truncate text-slate-200">{p.title}</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                      <span>{p.sku || p.category}</span>
                      {isSelected && <span className="text-cyan-400 font-semibold">ACTIVE</span>}
                    </div>
                  </button>
                );
              })
            ) : (
              <div className="p-3 text-center text-[11px] text-slate-500 italic">
                Loading catalog...
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-3 text-[11px] text-slate-400">
        <div className="flex items-center justify-between font-semibold text-slate-300 mb-1">
          <span>Engine Status</span>
          <span className="text-emerald-400">99.9% Uptime</span>
        </div>
        <p className="text-[10px] text-slate-500 leading-relaxed">
          SSRF Guard active • SQLite/PostgreSQL Sync • Real-Time OpenFX TTL: 12h
        </p>
      </div>
    </aside>
  );
};
