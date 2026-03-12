"use client";

import { useEffect, useState } from "react";
import { Bell, ShieldAlert, Save, Loader2, CheckCircle2 } from "lucide-react";
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

const FREQUENCY_PRESETS: Record<string, string> = {
  every_minute: "* * * * *",
  "daily-midnight": "0 0 * * *",
  "daily-noon": "0 12 * * *",
  weekly: "0 0 * * 1",
  monthly: "0 0 1 * *",
};

export default function SettingsPage() {
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

  // Initial load
  useEffect(() => {
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
    loadInitialData();
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

        // Ensure alertConfig is initialized even if null
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

        // Find existing schedule or set default
        const existing = schedulesData.find(
          (s) => s.dataset === selectedDatasetId
        );
        if (existing) {
          setSchedule(existing);
          // Try to match with preset
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
  }, [selectedDatasetId, FREQUENCY_PRESETS]);

  const handleSaveSettings = async () => {
    if (!selectedDatasetId || !alertConfig || !schedule) return;

    setSaving(true);
    try {
      // Save Alert Config
      const updatedAlert = await updateAlertConfig(selectedDatasetId, {
        threshold: alertConfig.threshold,
        email_notifications: alertConfig.email_notifications,
      });
      setAlertConfig(updatedAlert);

      // Save Schedule
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-primary" size={48} />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div>
        <h2 className="text-xl font-black text-[#08293c]">
          DATA QUALITY SETTINGS
        </h2>
        <p className="text-[12px] font-medium text-gray-400 mt-1">
          Manage thresholds, schedules, and alerts for your datasets.
        </p>
      </div>

      {/* Notification Preferences (Main objective) */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden ring-2 ring-accent/5 focus-within:ring-accent/20 transition-all">
        <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-accent/10 text-accent rounded-lg">
              <Bell size={20} />
            </div>
            <div>
              <h3 className="text-sm font-black text-[#08293c] uppercase tracking-widest leading-none">
                Data Quality Alerts
              </h3>
              <p className="text-[12px] font-medium text-gray-400 mt-1">
                Configure score thresholds and email notifications.
              </p>
            </div>
          </div>
          {saveSuccess && (
            <div className="flex items-center gap-2 text-success text-sm font-bold bg-success/10 px-3 py-1 rounded-full animate-in fade-in duration-500">
              <CheckCircle2 size={16} /> Saved Successfully
            </div>
          )}
        </div>

        <div className="p-6 space-y-8">
          {/* Dataset Selector for Alerts */}
          <div className="space-y-3">
            <label className="text-sm font-bold text-gray-700 block uppercase tracking-wider">
              Select Dataset to Configure
            </label>
            <select
              value={selectedDatasetId || ""}
              onChange={(e) => setSelectedDatasetId(Number(e.target.value))}
              className="w-full max-w-md px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent outline-none transition-all font-medium text-primary"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-400">
              Settings below will be applied to the selected dataset.
            </p>
          </div>

          <div className="h-px bg-gray-100" />

          {/* Email Alerts Toggle */}
          <div className="flex items-center justify-between group p-4 rounded-xl hover:bg-gray-50 transition-colors">
            <div>
              <h4 className="font-bold text-[#08293c]">Email Notifications</h4>
              <p className="text-sm text-gray-500">
                Receive an email when quality score drops below threshold.
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
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[4px] after:left-[4px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent shadow-inner"></div>
            </label>
          </div>

          {/* Quality Threshold Range */}
          <div className="space-y-6 pt-6 border-t border-gray-100 px-4">
            <div>
              <h4 className="font-bold text-[#08293c] flex items-center gap-2">
                Alert Threshold
              </h4>
              <p className="text-sm text-gray-500 mt-1">
                Only send alerts if the overall quality score falls below this
                percentage.
              </p>
            </div>

            <div className="flex items-center gap-8">
              <input
                type="range"
                min="0"
                max="100"
                value={alertConfig?.threshold ?? 80}
                onChange={(e) =>
                  setAlertConfig((prev) =>
                    prev ? { ...prev, threshold: Number(e.target.value) } : null
                  )
                }
                className="flex-1 h-3 bg-gray-100 rounded-full appearance-none cursor-pointer accent-[#ff5a00] outline-none"
              />
              <div className="min-w-[80px] h-12 flex items-center justify-center bg-primary text-white font-black text-lg rounded-xl shadow-lg shadow-primary/20">
                {alertConfig?.threshold ?? 80}%
              </div>
            </div>
            <div className="flex justify-between text-[10px] font-black text-gray-400 uppercase tracking-widest px-1">
              <span>Critical (0%)</span>
              <span>Perfect (100%)</span>
            </div>
          </div>
        </div>
      </section>

      {/* Scheduling Section */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden ring-2 ring-accent/5 focus-within:ring-accent/20 transition-all">
        <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
              <ShieldAlert size={20} />
            </div>
            <div>
              <h3 className="text-sm font-black text-[#08293c] uppercase tracking-widest leading-none">
                Automated Checks
              </h3>
              <p className="text-[12px] font-medium text-gray-400 mt-1">
                Schedule recurring quality validations.
              </p>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-8">
          <div className="space-y-4 px-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-bold text-gray-700 block uppercase tracking-wider">
                Check Frequency
              </label>
              <button
                onClick={() => setIsAdvanced(!isAdvanced)}
                className="text-[10px] font-black text-accent uppercase tracking-widest hover:underline"
              >
                {isAdvanced ? "Use Simple Form" : "Show Advanced (Cron)"}
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
                          ? { ...prev, cron_expression: FREQUENCY_PRESETS[key] }
                          : null
                      );
                    }}
                    className={`py-3 px-2 rounded-xl border-2 transition-all font-bold text-[11px] uppercase tracking-wider ${
                      frequency === key
                        ? "border-[#ff5a00] bg-[#ff5a00]/5 text-[#ff5a00]"
                        : "border-gray-100 bg-gray-50 text-gray-400 hover:border-gray-200"
                    }`}
                  >
                    {key.replace("-", " ").replace("_", " ")}
                  </button>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                <input
                  type="text"
                  placeholder="0 0 * * *"
                  value={schedule?.cron_expression || ""}
                  onChange={(e) =>
                    setSchedule((prev) =>
                      prev ? { ...prev, cron_expression: e.target.value } : null
                    )
                  }
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent outline-none transition-all font-mono text-primary text-center"
                />
                <p className="text-[10px] text-gray-400 font-medium text-center italic">
                  Format: minute hour day month weekday (e.g., 0 0 * * * for
                  daily).
                </p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Save Button Bar */}
      <div className="sticky bottom-6 flex justify-end">
        <button
          onClick={handleSaveSettings}
          disabled={saving || !selectedDatasetId}
          className="flex items-center gap-2 px-10 py-4 bg-[#ff5a00] text-white font-black rounded-2xl hover:shadow-xl hover:shadow-[#ff5a00]/30 transition-all active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none uppercase tracking-widest text-sm"
        >
          {saving ? (
            <Loader2 className="animate-spin" size={20} />
          ) : (
            <Save size={20} />
          )}
          {saving ? "Updating..." : "Save All Settings"}
        </button>
      </div>
    </div>
  );
}
