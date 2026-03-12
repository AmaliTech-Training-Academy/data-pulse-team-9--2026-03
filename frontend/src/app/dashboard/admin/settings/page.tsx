"use client";

import { useEffect, useState } from "react";
import {
  Settings,
  ShieldCheck,
  AlertCircle,
  Database,
  Bell,
  Save,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { getSystemHealth, SystemHealth } from "@/services/health";
import { getDatasets, Dataset } from "@/services/datasets";
import {
  getAlertConfig,
  updateAlertConfig,
  AlertConfig,
} from "@/services/alerts";
import {
  getSchedules,
  createOrUpdateSchedule,
  Schedule,
} from "@/services/schedules";

// Health polling interval removed if it were unused, but it is used.
// System health monitoring remains.

export default function AdminSettingsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(
    null
  );
  const [alertConfig, setAlertConfig] = useState<AlertConfig | null>(null);
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [frequency, setFrequency] = useState("daily-midnight");
  const [isAdvanced, setIsAdvanced] = useState(false);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [health, setHealth] = useState<SystemHealth | null>(null);

  const FREQUENCY_PRESETS: Record<string, string> = {
    every_minute: "* * * * *",
    "daily-midnight": "0 0 * * *",
    "daily-noon": "0 12 * * *",
    weekly: "0 0 * * 1",
    monthly: "0 0 1 * *",
  };

  useEffect(() => {
    const fetchHealth = async () => {
      const data = await getSystemHealth();
      setHealth(data);
    };

    const loadInitialData = async () => {
      try {
        const rawDatasets = await getDatasets();
        setDatasets(rawDatasets);
        if (rawDatasets.length > 0) {
          setSelectedDatasetId(rawDatasets[0].id);
        }
      } catch (err) {
        console.error("Failed to load settings data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
    loadInitialData();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Load alert config and schedule when selected dataset changes
  useEffect(() => {
    if (!selectedDatasetId) return;

    const loadConfig = async () => {
      try {
        const [alertData, schedulesData] = await Promise.all([
          getAlertConfig(selectedDatasetId),
          getSchedules(),
        ]);

        setAlertConfig(
          alertData || {
            id: 0,
            dataset_id: selectedDatasetId,
            threshold: 80,
            email_notifications: true,
            is_alert_active: false,
            created_at: "",
            updated_at: "",
          }
        );

        const existing = schedulesData.find(
          (s) => s.dataset === selectedDatasetId
        );
        if (existing) {
          setSchedule(existing);
          const presetValue = Object.keys(FREQUENCY_PRESETS).find(
            (key) => FREQUENCY_PRESETS[key] === existing.cron_expression
          );
          if (presetValue) {
            setFrequency(presetValue);
            setIsAdvanced(false);
          } else {
            setFrequency("custom");
            setIsAdvanced(true);
          }
        } else {
          setSchedule({
            dataset: selectedDatasetId,
            cron_expression: "0 0 * * *",
          });
          setFrequency("daily-midnight");
          setIsAdvanced(false);
        }
      } catch (err) {
        console.error("Failed to load dataset config:", err);
      }
    };

    loadConfig();
  }, [selectedDatasetId]);

  const handleSaveSettings = async () => {
    if (!selectedDatasetId || !alertConfig || !schedule) return;

    setSaving(true);
    try {
      const updatedAlert = await updateAlertConfig(selectedDatasetId, {
        threshold: alertConfig.threshold,
        email_notifications: alertConfig.email_notifications,
      });
      setAlertConfig(updatedAlert);

      const updatedSchedule = await createOrUpdateSchedule({
        dataset_id: selectedDatasetId,
        cron_expression: schedule.cron_expression,
      });
      setSchedule(updatedSchedule);

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to save settings:", err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12 animate-in fade-in duration-500">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-primary">System Settings</h2>
        <p className="text-gray-500">
          Configure global application parameters, notification rules, and
          monitor system activity.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Configuration */}
        <div className="lg:col-span-2 space-y-8">
          {/* Dataset Configuration */}
          <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-5 border-b border-gray-100 bg-gray-50/50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 text-primary rounded-lg">
                  <Bell size={20} />
                </div>
                <h3 className="text-lg font-bold text-primary">
                  Data Quality Alerts
                </h3>
              </div>
              {saveSuccess && (
                <div className="flex items-center gap-2 text-success text-sm font-bold bg-success/10 px-3 py-1 rounded-full">
                  <CheckCircle2 size={16} /> Saved Successfully
                </div>
              )}
            </div>

            <div className="p-6 space-y-8">
              <div className="space-y-3">
                <label className="text-sm font-bold text-gray-700 block uppercase tracking-wider">
                  Select Dataset to Configure
                </label>
                <select
                  value={selectedDatasetId || ""}
                  onChange={(e) => setSelectedDatasetId(Number(e.target.value))}
                  className="w-full max-w-md px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent outline-none"
                >
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="h-px bg-gray-100" />

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-primary">
                    Email Notifications
                  </h4>
                  <p className="text-sm text-gray-500">
                    Receive alerts when quality score drops below threshold.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={alertConfig?.email_notifications ?? true}
                    onChange={(e) =>
                      setAlertConfig((prev) =>
                        prev
                          ? { ...prev, email_notifications: e.target.checked }
                          : null
                      )
                    }
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent focus-within:ring-2 focus-within:ring-accent/20"></div>
                </label>
              </div>

              <div className="space-y-4 pt-4 border-t border-gray-100">
                <div className="flex justify-between items-center">
                  <h4 className="font-bold text-primary">Alert Threshold</h4>
                  <span className="font-black text-accent text-lg">
                    {alertConfig?.threshold ?? 80}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={alertConfig?.threshold ?? 80}
                  onChange={(e) =>
                    setAlertConfig((prev) =>
                      prev
                        ? { ...prev, threshold: Number(e.target.value) }
                        : null
                    )
                  }
                  className="w-full h-2 bg-gray-100 rounded-lg appearance-none cursor-pointer accent-accent"
                />
              </div>
            </div>
          </section>

          {/* Scheduling Section */}
          <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-5 border-b border-gray-100 bg-gray-50/50 flex items-center gap-3">
              <div className="p-2 bg-primary/10 text-primary rounded-lg">
                <Settings size={20} />
              </div>
              <h3 className="text-lg font-bold text-primary">
                Automated Checks
              </h3>
            </div>

            <div className="p-6 space-y-6">
              <div className="flex justify-between items-center">
                <label className="text-sm font-bold text-gray-700 uppercase tracking-wider">
                  Check Frequency
                </label>
                <button
                  onClick={() => setIsAdvanced(!isAdvanced)}
                  className="text-[10px] font-black text-accent uppercase tracking-widest hover:underline"
                >
                  {isAdvanced ? "Simple View" : "Advanced (Cron)"}
                </button>
              </div>

              {!isAdvanced ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                  {Object.keys(FREQUENCY_PRESETS).map((key) => (
                    <button
                      key={key}
                      onClick={() => {
                        setFrequency(key);
                        setSchedule((prev) =>
                          prev
                            ? {
                                ...prev,
                                cron_expression: FREQUENCY_PRESETS[key],
                              }
                            : null
                        );
                      }}
                      className={`py-2 px-1 rounded-lg border-2 transition-all font-bold text-[10px] uppercase tracking-tighter ${
                        frequency === key
                          ? "border-accent bg-accent/5 text-accent"
                          : "border-gray-100 bg-gray-50 text-gray-400 hover:border-gray-200"
                      }`}
                    >
                      {key.replace("-", " ").replace("_", " ")}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  <input
                    type="text"
                    placeholder="0 0 * * *"
                    value={schedule?.cron_expression || ""}
                    onChange={(e) =>
                      setSchedule((prev) =>
                        prev
                          ? { ...prev, cron_expression: e.target.value }
                          : null
                      )
                    }
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent outline-none font-mono text-center"
                  />
                  <p className="text-[10px] text-gray-400 text-center italic">
                    Format: minute hour day month weekday
                  </p>
                </div>
              )}
            </div>

            <div className="p-6 border-t border-gray-100 flex justify-end bg-gray-50/30">
              <button
                onClick={handleSaveSettings}
                disabled={saving || !selectedDatasetId}
                className="flex items-center gap-2 px-8 py-3 bg-primary text-white font-bold rounded-xl hover:shadow-lg transition-all active:scale-[0.98] disabled:opacity-50"
              >
                {saving ? (
                  <Loader2 className="animate-spin" size={18} />
                ) : (
                  <Save size={18} />
                )}
                {saving ? "Saving..." : "Save Configuration"}
              </button>
            </div>
          </section>
        </div>

        {/* Right Column - Status & Quick Actions */}
        <div className="lg:col-span-1 space-y-8">
          {/* System Health */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h4 className="font-bold text-primary mb-6 flex items-center gap-2">
              <ShieldCheck size={18} className="text-success" /> Platform Health
            </h4>
            <div className="space-y-6">
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <span className="text-xs font-bold text-gray-500 uppercase">
                    PostgreSQL Database
                  </span>
                  <span
                    className={`text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-tighter ${
                      health?.database === "up"
                        ? "bg-success/10 text-success"
                        : "bg-danger/10 text-danger"
                    }`}
                  >
                    {health?.database === "up" ? "Healthy" : "Down"}
                  </span>
                </div>
                <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      health?.database === "up"
                        ? "bg-success w-full"
                        : "bg-danger w-0"
                    }`}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <span className="text-xs font-bold text-gray-500 uppercase">
                    Redis Cache
                  </span>
                  <span
                    className={`text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-tighter ${
                      health?.redis === "up"
                        ? "bg-success/10 text-success"
                        : "bg-danger/10 text-danger"
                    }`}
                  >
                    {health?.redis === "up" ? "Connected" : "Disconnected"}
                  </span>
                </div>
                <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      health?.redis === "up"
                        ? "bg-success w-full"
                        : "bg-danger w-0"
                    }`}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
