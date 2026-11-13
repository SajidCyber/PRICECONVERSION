'use client';

import React, { useState, useEffect } from 'react';
import {
  Sliders,
  Calculator,
  RefreshCw,
  Sparkles,
  Zap,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
} from 'lucide-react';
import { LandedCostBreakdown } from '@/types';
import { apiClient } from '@/services/api';
import { fmt, fmtPct } from '@/utils/format';

export const LandedCostSimulatorView: React.FC = () => {
  const [price, setPrice] = useState<number>(1299.0);
  const [sourceCurrency, setSourceCurrency] = useState<string>('USD');
  const [destinationCountry, setDestinationCountry] = useState<string>('US');
  const [freight, setFreight] = useState<number>(25.0);
  const [dutyRate, setDutyRate] = useState<number>(0.05); // 5%
  const [taxRate, setTaxRate] = useState<number>(0.08); // 8%
  const [insuranceRate, setInsuranceRate] = useState<number>(0.01); // 1%
  const [handlingFee, setHandlingFee] = useState<number>(15.0);

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<LandedCostBreakdown | null>(null);

  useEffect(() => {
    runCalculation();
  }, [price, sourceCurrency, destinationCountry, freight, dutyRate, taxRate, insuranceRate, handlingFee]);

  const runCalculation = async () => {
    setLoading(true);
    try {
      const breakdown = await apiClient.simulateLandedCost({
        price: Number(price) || 0,
        source_currency: sourceCurrency,
        destination_country: destinationCountry,
        override_freight: Number(freight),
        override_duty_rate: Number(dutyRate),
        override_tax_rate: Number(taxRate),
        override_insurance_rate: Number(insuranceRate),
        override_handling_fee: Number(handlingFee),
      });
      setResult(breakdown);
    } catch {
      // Local fallback calculation if backend request pending
      const converted = price * (sourceCurrency === 'EUR' ? 1.08 : sourceCurrency === 'GBP' ? 1.30 : 1.0);
      const ins = converted * insuranceRate;
      const cif = converted + freight + ins;
      const duty = cif * dutyRate;
      const tax = (cif + duty) * taxRate;
      const total = cif + duty + tax + handlingFee;
      const markup = converted > 0 ? ((total - converted) / converted) * 100 : 0;

      setResult({
        original_price: price,
        original_currency: sourceCurrency,
        destination_currency: destinationCountry === 'GB' ? 'GBP' : destinationCountry === 'DE' ? 'EUR' : 'USD',
        fx_rate: 1.0,
        fx_source: 'fallback',
        is_fx_fallback: false,
        converted_price: converted,
        freight_fee: freight,
        insurance_fee: ins,
        cif_value: cif,
        de_minimis_threshold: 800,
        is_duty_exempt: false,
        customs_duty_rate: dutyRate,
        customs_duty_amount: duty,
        tax_base_value: cif + duty,
        import_tax_rate: taxRate,
        import_tax_amount: tax,
        handling_fee: handlingFee,
        total_landed_cost: total,
        effective_markup_pct: markup,
        assumptions_log: {},
      });
    } finally {
      setLoading(false);
    }
  };

  const handleResetDefaults = () => {
    setPrice(1299.0);
    setSourceCurrency('USD');
    setDestinationCountry('US');
    setFreight(25.0);
    setDutyRate(0.05);
    setTaxRate(0.08);
    setInsuranceRate(0.01);
    setHandlingFee(15.0);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-gradient-to-r from-white/[0.05] via-[#080d1e] to-[#040814] p-6 backdrop-blur-2xl shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-cyan-500/20 to-indigo-500/20 border border-cyan-500/30 text-cyan-300 shadow-[0_0_20px_rgba(6,182,212,0.2)]">
              <Calculator className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-xl font-black text-white tracking-tight">
                Orbital Landed Cost & Tariff Simulator
              </h2>
              <p className="text-xs text-slate-400">
                Live econometric sensitivity model for international customs, freight, VAT/GST, and FX spreads
              </p>
            </div>
          </div>

          <button
            onClick={handleResetDefaults}
            className="flex items-center gap-1.5 self-start sm:self-auto rounded-xl border border-white/[0.1] bg-white/[0.04] px-3.5 py-2 text-xs font-semibold text-slate-300 hover:text-white hover:border-cyan-500/40 transition cursor-pointer"
          >
            <RotateCcw className="h-3.5 w-3.5 text-cyan-400" />
            <span>Reset Defaults</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form: Parameter Inputs & Sliders (7 cols) */}
        <div className="lg:col-span-7 rounded-3xl border border-white/[0.08] bg-gradient-to-b from-white/[0.04] to-transparent p-6 space-y-6 backdrop-blur-2xl shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
            <h3 className="text-sm font-extrabold text-white flex items-center gap-2">
              <Sliders className="h-4 w-4 text-cyan-400" />
              Dynamic Cost Parameters & Tariff Overrides
            </h3>
            <span className="text-[10px] text-cyan-300 font-mono font-bold bg-cyan-500/10 px-2 py-0.5 rounded-full border border-cyan-500/20">
              REACTIVE
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 text-xs">
            {/* Price */}
            <div>
              <label className="text-slate-400 font-semibold block mb-1.5">Sticker Price</label>
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(Number(e.target.value))}
                className="w-full rounded-2xl border border-white/[0.1] bg-black/40 p-3 text-white font-mono font-bold focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400/50 transition"
              />
            </div>

            {/* Source Currency */}
            <div>
              <label className="text-slate-400 font-semibold block mb-1.5">Source Currency</label>
              <select
                value={sourceCurrency}
                onChange={(e) => setSourceCurrency(e.target.value)}
                className="w-full rounded-2xl border border-white/[0.1] bg-black/40 p-3 text-white font-semibold focus:border-cyan-400 focus:outline-none cursor-pointer transition"
              >
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
                <option value="INR">INR (₹)</option>
                <option value="JPY">JPY (¥)</option>
              </select>
            </div>

            {/* Destination Country */}
            <div>
              <label className="text-slate-400 font-semibold block mb-1.5">Destination Jurisdiction</label>
              <select
                value={destinationCountry}
                onChange={(e) => setDestinationCountry(e.target.value)}
                className="w-full rounded-2xl border border-white/[0.1] bg-black/40 p-3 text-white font-semibold focus:border-cyan-400 focus:outline-none cursor-pointer transition"
              >
                <option value="US">🇺🇸 United States</option>
                <option value="GB">🇬🇧 United Kingdom</option>
                <option value="DE">🇩🇪 Germany / EU</option>
                <option value="IN">🇮🇳 India</option>
                <option value="JP">🇯🇵 Japan</option>
              </select>
            </div>
          </div>

          {/* Sliders Grid */}
          <div className="space-y-5 pt-3 border-t border-white/[0.08] text-xs">
            {/* Freight */}
            <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
              <div className="flex justify-between text-slate-300 font-semibold mb-2">
                <span>International Freight & Transport</span>
                <span className="font-mono text-cyan-300 font-bold bg-cyan-500/10 px-2 py-0.5 rounded-md border border-cyan-500/20">
                  ${freight.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="150"
                step="5"
                value={freight}
                onChange={(e) => setFreight(Number(e.target.value))}
                className="w-full cursor-pointer"
              />
            </div>

            {/* Customs Duty */}
            <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
              <div className="flex justify-between text-slate-300 font-semibold mb-2">
                <span>Customs Tariff Rate</span>
                <span className="font-mono text-indigo-300 font-bold bg-indigo-500/10 px-2 py-0.5 rounded-md border border-indigo-500/20">
                  {(dutyRate * 100).toFixed(1)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="0.30"
                step="0.005"
                value={dutyRate}
                onChange={(e) => setDutyRate(Number(e.target.value))}
                className="w-full cursor-pointer"
              />
            </div>

            {/* Import Tax / VAT */}
            <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
              <div className="flex justify-between text-slate-300 font-semibold mb-2">
                <span>Destination Import VAT / GST</span>
                <span className="font-mono text-rose-300 font-bold bg-rose-500/10 px-2 py-0.5 rounded-md border border-rose-500/20">
                  {(taxRate * 100).toFixed(1)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="0.25"
                step="0.005"
                value={taxRate}
                onChange={(e) => setTaxRate(Number(e.target.value))}
                className="w-full cursor-pointer"
              />
            </div>

            {/* Handling Fee */}
            <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
              <div className="flex justify-between text-slate-300 font-semibold mb-2">
                <span>Customs Handling & Clearance Fee</span>
                <span className="font-mono text-amber-300 font-bold bg-amber-500/10 px-2 py-0.5 rounded-md border border-amber-500/20">
                  ${handlingFee.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                step="2.5"
                value={handlingFee}
                onChange={(e) => setHandlingFee(Number(e.target.value))}
                className="w-full cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Right Column: Real-Time Landed Cost Output (5 cols) */}
        <div className="lg:col-span-5 rounded-3xl border border-indigo-500/30 bg-gradient-to-br from-[#0c1024] via-[#070b18] to-[#040714] p-6 space-y-5 shadow-2xl backdrop-blur-2xl">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
            <h3 className="text-sm font-extrabold text-white flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-cyan-400" />
              Real-Time Landed Valuation
            </h3>
            {loading && <RefreshCw className="h-3.5 w-3.5 animate-spin text-cyan-400" />}
          </div>

          {result && (
            <div className="space-y-5">
              {/* Grand Total Landed Cost Display */}
              <div className="relative overflow-hidden rounded-3xl border border-emerald-500/40 bg-gradient-to-b from-emerald-500/15 via-emerald-500/5 to-transparent p-6 text-center shadow-[0_0_30px_rgba(16,185,129,0.15)]">
                <span className="text-[10px] uppercase font-black tracking-widest text-emerald-400 block mb-1">
                  ESTIMATED LANDED BURDEN IN {result.destination_currency}
                </span>
                <div className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-emerald-300 via-white to-emerald-200 font-mono">
                  {result.destination_currency} {fmt(result.total_landed_cost, 2)}
                </div>
                <div className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-500/20 px-3 py-0.5 text-xs font-bold text-emerald-300 border border-emerald-500/30">
                  <Zap className="h-3 w-3" />
                  {fmtPct(result.effective_markup_pct, 1)} Total Landed Markup
                </div>
              </div>

              {/* Stack Breakdown Line Items */}
              <div className="space-y-2.5 text-xs font-mono">
                <div className="flex justify-between items-center text-slate-300 py-1.5 px-3 rounded-xl bg-white/[0.02]">
                  <span className="text-slate-400 font-sans">1. Converted Base Price</span>
                  <span className="font-bold">${fmt(result.converted_price, 2)}</span>
                </div>
                <div className="flex justify-between items-center text-slate-300 py-1.5 px-3 rounded-xl bg-white/[0.02]">
                  <span className="text-slate-400 font-sans">2. Freight & Logistics</span>
                  <span className="text-cyan-300 font-bold">+${fmt(result.freight_fee, 2)}</span>
                </div>
                <div className="flex justify-between items-center text-slate-300 py-1.5 px-3 rounded-xl bg-white/[0.02]">
                  <span className="text-slate-400 font-sans">3. Cargo Insurance</span>
                  <span className="text-cyan-300 font-bold">+${fmt(result.insurance_fee, 2)}</span>
                </div>
                <div className="flex justify-between items-center text-white font-extrabold py-2 px-3 bg-gradient-to-r from-indigo-500/20 to-cyan-500/10 rounded-xl border border-indigo-500/30 shadow-inner">
                  <span className="font-sans text-cyan-200">CIF Assessment Value</span>
                  <span className="text-white">${fmt(result.cif_value, 2)}</span>
                </div>
                <div className="flex justify-between items-center text-slate-300 py-1.5 px-3 rounded-xl bg-white/[0.02]">
                  <span className="text-slate-400 font-sans">4. Customs Duty Tariff</span>
                  <span className="text-indigo-300 font-bold">+${fmt(result.customs_duty_amount, 2)}</span>
                </div>
                <div className="flex justify-between items-center text-slate-300 py-1.5 px-3 rounded-xl bg-white/[0.02]">
                  <span className="text-slate-400 font-sans">5. Import VAT / GST</span>
                  <span className="text-rose-300 font-bold">+${fmt(result.import_tax_amount, 2)}</span>
                </div>
                <div className="flex justify-between items-center text-slate-300 py-1.5 px-3 rounded-xl bg-white/[0.02]">
                  <span className="text-slate-400 font-sans">6. Clearance Surcharges</span>
                  <span className="text-amber-300 font-bold">+${fmt(result.handling_fee, 2)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

