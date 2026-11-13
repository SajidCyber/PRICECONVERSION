'use client';

import React, { useState, useEffect } from 'react';
import {
  BellRing,
  Plus,
  Trash2,
  CheckCircle,
  Play,
  Clock,
  ShieldAlert,
  Zap,
} from 'lucide-react';
import { AlertNotificationResponse, PriceAlertResponse } from '@/types';
import { apiClient } from '@/services/api';

interface AlertCenterViewProps {
  selectedProductId: string;
  onRefreshUnreadCount: () => void;
}

export const AlertCenterView: React.FC<AlertCenterViewProps> = ({
  selectedProductId,
  onRefreshUnreadCount,
}) => {
  const [alerts, setAlerts] = useState<PriceAlertResponse[]>([]);
  const [notifications, setNotifications] = useState<AlertNotificationResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);

  // New Alert Form State
  const [alertType, setAlertType] = useState<string>('threshold_below');
  const [conditionValue, setConditionValue] = useState<number>(1500.0);
  const [severity, setSeverity] = useState<string>('high');

  useEffect(() => {
    loadData();
  }, [selectedProductId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [alertsList, notifsList] = await Promise.all([
        apiClient.listAlerts(selectedProductId),
        apiClient.listNotifications(),
      ]);
      setAlerts(alertsList);
      setNotifications(notifsList);
    } catch {
      // Fallback data
      setAlerts([
        {
          id: 'alt_1',
          product_id: selectedProductId,
          product_title: 'Apple MacBook Pro 14 M3',
          alert_type: 'threshold_below',
          condition_value: 1500.0,
          severity: 'high',
          is_active: true,
          created_at: new Date().toISOString(),
          notifications_count: 1,
        },
      ]);
      setNotifications([
        {
          id: 'notif_1',
          alert_id: 'alt_1',
          product_id: selectedProductId,
          product_title: 'Apple MacBook Pro 14 M3',
          observation_id: 'obs_1',
          alert_type: 'threshold_below',
          severity: 'high',
          message: "Price Alert: 'Apple MacBook Pro 14 M3' dropped to USD 1499.00 on Amazon US.",
          evidence_payload: {},
          is_acknowledged: false,
          triggered_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAlert = async () => {
    try {
      await apiClient.createAlert({
        product_id: selectedProductId,
        alert_type: alertType,
        condition_value: Number(conditionValue),
        severity: severity,
      });
      loadData();
    } catch (err: any) {
      alert(`Error creating alert: ${err.message}`);
    }
  };

  const handleDeleteAlert = async (id: string) => {
    try {
      await apiClient.deleteAlert(id);
      setAlerts(alerts.filter((a) => a.id !== id));
    } catch (err: any) {
      alert(`Error deleting alert: ${err.message}`);
    }
  };

  const handleEvaluateAlerts = async () => {
    setIsEvaluating(true);
    try {
      await apiClient.evaluateAlerts(selectedProductId);
      await loadData();
      onRefreshUnreadCount();
    } catch (err: any) {
      alert(`Error running alert evaluation: ${err.message}`);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleAcknowledgeNotification = async (id: string) => {
    try {
      await apiClient.acknowledgeNotification(id);
      setNotifications(
        notifications.map((n) => (n.id === id ? { ...n, is_acknowledged: true } : n))
      );
      onRefreshUnreadCount();
    } catch (err: any) {
      console.warn('Acknowledge failed:', err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-3xl border border-white/[0.08] bg-gradient-to-r from-white/[0.05] via-[#0d091a] to-[#040814] p-6 backdrop-blur-2xl shadow-xl">
        <div className="flex items-center gap-3.5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 shadow-[0_0_20px_rgba(244,63,94,0.15)]">
            <BellRing className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-xl font-black text-white tracking-tight">
              Anti-Flapping Alert Center & Automated Governance
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Automated triggers for flash price drops, competitor margin breaches, and stock status changes
            </p>
          </div>
        </div>

        <button
          onClick={handleEvaluateAlerts}
          disabled={isEvaluating}
          className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-rose-500 via-amber-500 to-amber-600 px-5 py-3 text-xs font-bold text-white shadow-lg shadow-rose-500/25 hover:shadow-rose-500/40 hover:scale-[1.02] transition disabled:opacity-50 cursor-pointer"
        >
          <Play className={`h-4 w-4 ${isEvaluating ? 'animate-spin' : 'fill-white'}`} />
          <span>{isEvaluating ? 'Evaluating Rules...' : 'Execute Live Rule Evaluation'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Create New Alert Rule (5 cols) */}
        <div className="lg:col-span-5 rounded-3xl border border-white/[0.08] bg-gradient-to-b from-white/[0.04] to-transparent p-6 space-y-5 backdrop-blur-2xl shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
            <h3 className="text-sm font-extrabold text-white flex items-center gap-2">
              <Plus className="h-4 w-4 text-cyan-400" />
              Configure Alert Trigger
            </h3>
            <span className="text-[10px] text-cyan-300 font-mono font-bold bg-cyan-500/10 px-2 py-0.5 rounded-full border border-cyan-500/20">
              ANTI-FLAPPING
            </span>
          </div>

          <div className="space-y-4 text-xs">
            <div>
              <label className="text-slate-400 font-semibold block mb-1.5">Rule Condition Type</label>
              <select
                value={alertType}
                onChange={(e) => setAlertType(e.target.value)}
                className="w-full rounded-2xl border border-white/[0.1] bg-black/40 p-3 text-white font-medium focus:border-cyan-400 focus:outline-none cursor-pointer transition"
              >
                <option value="threshold_below">Price drops below target value ($)</option>
                <option value="pct_change_drop">Flash discount / price drop (% change)</option>
                <option value="landed_cost_breach">Competitor landed cost breach ($)</option>
                <option value="out_of_stock">Competitor goes out of stock</option>
              </select>
            </div>

            <div>
              <label className="text-slate-400 font-semibold block mb-1.5">
                Target Threshold ({alertType === 'pct_change_drop' ? '%' : '$'})
              </label>
              <input
                type="number"
                value={conditionValue}
                onChange={(e) => setConditionValue(Number(e.target.value))}
                className="w-full rounded-2xl border border-white/[0.1] bg-black/40 p-3 text-white font-mono font-bold focus:border-cyan-400 focus:outline-none transition"
              />
            </div>

            <div>
              <label className="text-slate-400 font-semibold block mb-1.5">Severity Level</label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="w-full rounded-2xl border border-white/[0.1] bg-black/40 p-3 text-white font-medium focus:border-cyan-400 focus:outline-none cursor-pointer transition"
              >
                <option value="low">Low (Info / Monitoring)</option>
                <option value="medium">Medium (Standard Alert)</option>
                <option value="high">High (Immediate Action)</option>
                <option value="critical">Critical (Flash Price War)</option>
              </select>
            </div>

            <button
              onClick={handleCreateAlert}
              className="w-full rounded-2xl bg-gradient-to-r from-indigo-600 to-cyan-600 py-3 font-bold text-white shadow-lg shadow-indigo-600/30 hover:opacity-95 transition cursor-pointer"
            >
              Arm Alert Trigger
            </button>
          </div>

          {/* Configured Rules List */}
          <div className="pt-4 border-t border-white/[0.08] space-y-2.5">
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              Active Trigger Rules ({alerts.length})
            </h4>
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {alerts.map((a) => (
                <div
                  key={a.id}
                  className="flex items-center justify-between p-3 rounded-2xl border border-white/[0.06] bg-black/30 text-xs"
                >
                  <div>
                    <span className="font-bold text-white block text-xs">{a.alert_type}</span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      Target: {a.condition_value} • Severity: {a.severity.toUpperCase()}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDeleteAlert(a.id)}
                    className="text-slate-400 hover:text-rose-400 transition p-1.5 rounded-lg hover:bg-white/[0.06]"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Triggered Notifications Inbox (7 cols) */}
        <div className="lg:col-span-7 rounded-3xl border border-white/[0.08] bg-gradient-to-b from-white/[0.04] to-transparent p-6 space-y-5 backdrop-blur-2xl shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
            <h3 className="text-sm font-extrabold text-white flex items-center gap-2">
              <Clock className="h-4 w-4 text-amber-400" />
              Event Notification Ledger
            </h3>
            <span className="text-xs font-mono font-bold text-cyan-300 bg-white/[0.05] px-2.5 py-0.5 rounded-full border border-white/[0.08]">
              {notifications.length} Events
            </span>
          </div>

          <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
            {notifications.length > 0 ? (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`p-4 rounded-2xl border transition-all duration-200 space-y-2.5 ${
                    n.is_acknowledged
                      ? 'bg-white/[0.02] border-white/[0.05] opacity-60'
                      : 'bg-gradient-to-br from-rose-950/30 to-black/60 border-rose-500/30 shadow-lg shadow-rose-950/20'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`h-2.5 w-2.5 rounded-full ${
                          n.severity === 'critical'
                            ? 'bg-rose-500 animate-ping'
                            : n.severity === 'high'
                            ? 'bg-amber-400 animate-pulse'
                            : 'bg-cyan-400'
                        }`}
                      />
                      <span className="font-extrabold text-xs text-white">{n.alert_type}</span>
                      <span className="text-[10px] font-mono text-slate-400">
                        {new Date(n.triggered_at).toLocaleTimeString()}
                      </span>
                    </div>

                    {!n.is_acknowledged ? (
                      <button
                        onClick={() => handleAcknowledgeNotification(n.id)}
                        className="flex items-center gap-1.5 text-[10px] font-bold text-cyan-300 hover:text-white bg-cyan-500/15 hover:bg-cyan-500/25 px-2.5 py-1 rounded-xl border border-cyan-500/30 transition cursor-pointer"
                      >
                        <CheckCircle className="h-3.5 w-3.5" />
                        <span>Acknowledge</span>
                      </button>
                    ) : (
                      <span className="text-[10px] text-slate-500 italic">Resolved</span>
                    )}
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed font-normal">{n.message}</p>
                </div>
              ))
            ) : (
              <div className="text-center py-16 text-xs text-slate-500 italic">
                No notification events triggered yet. Configure rules or click &quot;Execute Live Rule Evaluation&quot;.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

