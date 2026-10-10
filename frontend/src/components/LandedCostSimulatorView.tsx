'use client';

import React, { useState, useEffect } from 'react';
import {
  Sliders,
  Calculator,
  RefreshCw,
  HelpCircle,
  ShieldCheck,
  Percent,
  DollarSign,
  Ship,
  Sparkles,
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

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <Calculator className="h-5 w-5 text-cyan-400" />
          <div>
            <h2 className="text-base font-bold text-white">Cross-Border Landed Cost & Tariff Simulator</h2>
            <p className="text-xs text-slate-400">
              Sensitivity calculator for customs tariffs, de minimis thresholds, import taxes, freight, and currency risk
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form: Parameter Inputs & Sliders (7 cols) */}
        <div className="lg:col-span-7 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-5 backdrop-blur-md">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Sliders className="h-4 w-4 text-indigo-400" />
            Cost Parameters & Tariff Overrides
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            {/* Price */}
            <div>
              <label className="text-slate-400 font-medium block mb-1">Sticker Base Price</label>
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(Number(e.target.value))}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-white font-mono focus:border-cyan-400 focus:outline-none"
              />
            </div>

            {/* Source Currency */}
            <div>
              <label className="text-slate-400 font-medium block mb-1">Source Currency</label>
              <select
                value={sourceCurrency}
                onChange={(e) => setSourceCurrency(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-white focus:border-cyan-400 focus:outline-none cursor-pointer"
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
              <label className="text-slate-400 font-medium block mb-1">Destination Market</label>
              <select
                value={destinationCountry}
                onChange={(e) => setDestinationCountry(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-white focus:border-cyan-400 focus:outline-none cursor-pointer"
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
          <div className="space-y-4 pt-2 border-t border-slate-800 text-xs">
            {/* Freight */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium mb-1">
                <span>International Freight / Shipping Fee</span>
                <span className="font-mono text-cyan-400 font-bold">${freight.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="150"
                step="5"
                value={freight}
                onChange={(e) => setFreight(Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>

            {/* Customs Duty */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium mb-1">
                <span>Customs Duty Tariff Rate</span>
                <span className="font-mono text-indigo-400 font-bold">{(dutyRate * 100).toFixed(1)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="0.30"
                step="0.005"
                value={dutyRate}
                onChange={(e) => setDutyRate(Number(e.target.value))}
                className="w-full accent-indigo-400 cursor-pointer"
              />
            </div>

            {/* Import Tax / VAT */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium mb-1">
                <span>Import VAT / GST Rate</span>
                <span className="font-mono text-rose-400 font-bold">{(taxRate * 100).toFixed(1)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="0.25"
                step="0.005"
                value={taxRate}
                onChange={(e) => setTaxRate(Number(e.target.value))}
                className="w-full accent-rose-400 cursor-pointer"
              />
            </div>

            {/* Handling Fee */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium mb-1">
                <span>Customs Brokerage & Clearance Fee</span>
                <span className="font-mono text-amber-400 font-bold">${handlingFee.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                step="2.5"
                value={handlingFee}
                onChange={(e) => setHandlingFee(Number(e.target.value))}
                className="w-full accent-amber-400 cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Right Column: Real-Time Landed Cost Output (5 cols) */}
        <div className="lg:col-span-5 rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/40 p-5 space-y-4 shadow-xl backdrop-blur-md">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
              <Sparkles className="h-4 w-4 text-cyan-400" />
              Landed Cost Stack
            </h3>
            {loading && <RefreshCw className="h-3.5 w-3.5 animate-spin text-cyan-400" />}
          </div>

          {result && (
            <div className="space-y-4">
              {/* Grand Total Landed Cost Display */}
              <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-center">
                <span className="text-[11px] uppercase font-bold text-emerald-400 block tracking-wider">
                  Total Landed Cost in {result.destination_currency}
                </span>
                <div className="text-3xl font-black text-emerald-300 font-mono mt-1">
                  {result.destination_currency} {fmt(result.total_landed_cost, 2)}
                </div>
                <span className="text-xs text-emerald-400/80 font-medium mt-1 block">
                  {fmtPct(result.effective_markup_pct, 1)} total landed markup over sticker price
                </span>
              </div>

              {/* Stack Breakdown Line Items */}
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between text-slate-300 py-1 border-b border-slate-800">
                  <span className="text-slate-400 font-sans">1. Converted Sticker Price</span>
                  <span>${fmt(result.converted_price, 2)}</span>
                </div>
                <div className="flex justify-between text-slate-300 py-1 border-b border-slate-800">
                  <span className="text-slate-400 font-sans">2. Freight & Logistics</span>
                  <span className="text-cyan-400">+${fmt(result.freight_fee, 2)}</span>
                </div>
                <div className="flex justify-between text-slate-300 py-1 border-b border-slate-800">
                  <span className="text-slate-400 font-sans">3. Marine / Cargo Insurance</span>
                  <span className="text-cyan-400">+${fmt(result.insurance_fee, 2)}</span>
                </div>
                <div className="flex justify-between text-slate-200 font-bold py-1 bg-slate-950/60 px-2 rounded">
                  <span className="font-sans">CIF Assessment Value</span>
                  <span>${fmt(result.cif_value, 2)}</span>
                </div>
                <div className="flex justify-between text-slate-300 py-1 border-b border-slate-800">
                  <span className="text-slate-400 font-sans">4. Customs Duty</span>
                  <span className="text-indigo-400">+${fmt(result.customs_duty_amount, 2)}</span>
                </div>
                <div className="flex justify-between text-slate-300 py-1 border-b border-slate-800">
                  <span className="text-slate-400 font-sans">5. Import VAT / GST</span>
                  <span className="text-rose-400">+${fmt(result.import_tax_amount, 2)}</span>
                </div>
                <div className="flex justify-between text-slate-300 py-1 border-b border-slate-800">
                  <span className="text-slate-400 font-sans">6. Clearance Handling Fee</span>
                  <span className="text-amber-400">+${fmt(result.handling_fee, 2)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
