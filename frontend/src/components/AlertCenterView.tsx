'use client';

import React, { useState, useEffect } from 'react';
import {
  BellRing,
  Plus,
  Trash2,
  CheckCircle,
  Play,
  AlertTriangle,
  Flame,
  Clock,
  ShieldAlert,
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2">
            <BellRing className="h-5 w-5 text-rose-400" />
            <h2 className="text-base font-bold text-white">Price Alerts & Real-Time Trigger Center</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure automated threshold monitors, flash drop detectors, and stock breach notifications
          </p>
        </div>

        <button
          onClick={handleEvaluateAlerts}
          disabled={isEvaluating}
          className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-rose-500 to-amber-500 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-rose-500/20 hover:opacity-90 transition disabled:opacity-50 cursor-pointer"
        >
          <Play className={`h-3.5 w-3.5 ${isEvaluating ? 'animate-spin' : 'fill-white'}`} />
          <span>{isEvaluating ? 'Evaluating Rules...' : 'Run Rules Evaluation'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Create New Alert Rule (5 cols) */}
        <div className="lg:col-span-5 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 backdrop-blur-md">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Plus className="h-4 w-4 text-cyan-400" />
            Create Alert Rule
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 font-medium block mb-1">Rule Condition Type</label>
              <select
                value={alertType}
                onChange={(e) => setAlertType(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-white focus:border-cyan-400 focus:outline-none cursor-pointer"
              >
                <option value="threshold_below">Price drops below target value ($)</option>
                <option value="pct_change_drop">Flash discount / price drop (% change)</option>
                <option value="landed_cost_breach">Competitor landed cost breach ($)</option>
                <option value="out_of_stock">Competitor goes out of stock</option>
              </select>
            </div>

            <div>
              <label className="text-slate-400 font-medium block mb-1">
                Threshold Target Value ({alertType === 'pct_change_drop' ? '%' : '$'})
              </label>
              <input
                type="number"
                value={conditionValue}
                onChange={(e) => setConditionValue(Number(e.target.value))}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-white font-mono focus:border-cyan-400 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-slate-400 font-medium block mb-1">Severity Tier</label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-white focus:border-cyan-400 focus:outline-none cursor-pointer"
              >
                <option value="low">Low (Info / Monitoring)</option>
                <option value="medium">Medium (Standard Alert)</option>
                <option value="high">High (Immediate Action)</option>
                <option value="critical">Critical (Flash War / Under-cutting)</option>
              </select>
            </div>

            <button
              onClick={handleCreateAlert}
              className="w-full rounded-xl bg-indigo-600 py-2.5 font-semibold text-white shadow-md shadow-indigo-600/30 hover:bg-indigo-500 transition cursor-pointer"
            >
              Add Alert Rule
            </button>
          </div>

          {/* Configured Rules List */}
          <div className="pt-4 border-t border-slate-800 space-y-2">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Active Rules ({alerts.length})
            </h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {alerts.map((a) => (
                <div
                  key={a.id}
                  className="flex items-center justify-between p-2.5 rounded-xl border border-slate-800 bg-slate-950/80 text-xs"
                >
                  <div>
                    <span className="font-semibold text-white block">{a.alert_type}</span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      Target: {a.condition_value} • Severity: {a.severity.toUpperCase()}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDeleteAlert(a.id)}
                    className="text-slate-500 hover:text-rose-400 transition p-1"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Triggered Notifications Inbox (7 cols) */}
        <div className="lg:col-span-7 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Clock className="h-4 w-4 text-amber-400" />
              Triggered Notification Inbox
            </h3>
            <span className="text-xs font-mono text-slate-400">{notifications.length} Events</span>
          </div>

          <div className="space-y-2.5 max-h-[460px] overflow-y-auto">
            {notifications.length > 0 ? (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`p-3.5 rounded-xl border transition space-y-2 ${
                    n.is_acknowledged
                      ? 'bg-slate-950/40 border-slate-800/60 opacity-60'
                      : 'bg-slate-950 border-rose-500/30 shadow-lg shadow-rose-950/20'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`h-2 w-2 rounded-full ${
                          n.severity === 'critical'
                            ? 'bg-rose-500'
                            : n.severity === 'high'
                            ? 'bg-amber-500'
                            : 'bg-cyan-500'
                        }`}
                      />
                      <span className="font-bold text-xs text-white">{n.alert_type}</span>
                      <span className="text-[10px] font-mono text-slate-500">{new Date(n.triggered_at).toLocaleTimeString()}</span>
                    </div>

                    {!n.is_acknowledged ? (
                      <button
                        onClick={() => handleAcknowledgeNotification(n.id)}
                        className="flex items-center gap-1 text-[10px] font-semibold text-cyan-400 hover:text-cyan-300 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20 transition cursor-pointer"
                      >
                        <CheckCircle className="h-3 w-3" />
                        <span>Acknowledge</span>
                      </button>
                    ) : (
                      <span className="text-[10px] text-slate-500 italic">Acknowledged</span>
                    )}
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">{n.message}</p>
                </div>
              ))
            ) : (
              <div className="text-center py-12 text-xs text-slate-500">
                No notification events triggered yet. Configure rules or click &quot;Run Rules Evaluation&quot;.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
