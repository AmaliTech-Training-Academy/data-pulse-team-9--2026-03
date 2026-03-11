"use client";

import { useEffect, useState } from "react";
import {
    User,
    Bell,
    ShieldAlert,
    Save,
    Loader2,
    CheckCircle2
} from "lucide-react";
import { getDatasets, Dataset } from "@/services/datasets";
import { getAlertConfig, updateAlertConfig, AlertConfig } from "@/services/alerts";

export default function SettingsPage() {
    const [datasets, setDatasets] = useState<Dataset[]>([]);
    const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
    const [alertConfig, setAlertConfig] = useState<AlertConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);

    // Initial load
    useEffect(() => {
        const loadInitialData = async () => {
            try {
                const data = await getDatasets();
                setDatasets(data);
                if (data.length > 0) {
                    setSelectedDatasetId(data[0].id);
                }
            } catch (err) {
                console.error("Failed to load settings data:", err);
            } finally {
                setLoading(false);
            }
        };
        loadInitialData();
    }, []);

    // Load alert config when selected dataset changes
    useEffect(() => {
        if (!selectedDatasetId) return;

        const loadAlertConfig = async () => {
            const config = await getAlertConfig(selectedDatasetId);
            setAlertConfig(config);
        };
        loadAlertConfig();
    }, [selectedDatasetId]);

    const handleSaveAlerts = async () => {
        if (!selectedDatasetId || !alertConfig) return;

        setSaving(true);
        try {
            const updated = await updateAlertConfig(selectedDatasetId, {
                threshold: alertConfig.threshold,
                email_notifications: alertConfig.email_notifications
            });
            setAlertConfig(updated);
            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 3000);
        } catch (err) {
            console.error("Failed to update alert config:", err);
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
                <h2 className="text-2xl font-bold text-primary">Account Settings</h2>
                <p className="text-gray-500">Manage your profile, preferences, and quality alerts.</p>
            </div>

            {/* Notification Preferences (Main objective) */}
            <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden ring-2 ring-accent/5 focus-within:ring-accent/20 transition-all">
                <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-accent/10 text-accent rounded-lg">
                            <Bell size={20} />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-primary">Data Quality Alerts</h3>
                            <p className="text-sm text-gray-500">Configure score thresholds and email notifications.</p>
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
                        <label className="text-sm font-bold text-gray-700 block uppercase tracking-wider">Select Dataset to Configure</label>
                        <select
                            value={selectedDatasetId || ""}
                            onChange={(e) => setSelectedDatasetId(Number(e.target.value))}
                            className="w-full max-w-md px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent outline-none transition-all font-medium text-primary"
                        >
                            {datasets.map(d => (
                                <option key={d.id} value={d.id}>{d.name}</option>
                            ))}
                        </select>
                        <p className="text-xs text-gray-400">Settings below will be applied to the selected dataset.</p>
                    </div>

                    <div className="h-px bg-gray-100" />

                    {/* Email Alerts Toggle */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-semibold text-gray-800">Email Notifications</h4>
                            <p className="text-sm text-gray-500">Receive an email when quality score drops below threshold.</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input
                                type="checkbox"
                                className="sr-only peer"
                                checked={alertConfig?.email_notifications ?? true}
                                onChange={(e) => setAlertConfig(prev => prev ? {...prev, email_notifications: e.target.checked} : null)}
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                        </label>
                    </div>

                    {/* Quality Threshold Range */}
                    <div className="space-y-4 pt-4 border-t border-gray-100">
                        <div>
                            <h4 className="font-semibold text-gray-800 flex items-center gap-2">
                                Alert Threshold
                            </h4>
                            <p className="text-sm text-gray-500 mt-1">Only send alerts if the overall quality score falls below this percentage.</p>
                        </div>

                        <div className="flex items-center gap-6 max-w-xl">
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={alertConfig?.threshold ?? 80}
                                onChange={(e) => setAlertConfig(prev => prev ? {...prev, threshold: Number(e.target.value)} : null)}
                                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-accent"
                            />
                            <span className="font-extrabold text-primary w-12 text-right">{alertConfig?.threshold ?? 80}%</span>
                        </div>
                        <p className="text-xs font-medium text-gray-400">Currently set to alert you if score drops below {alertConfig?.threshold ?? 80}%.</p>
                    </div>

                    <div className="pt-6 border-t border-gray-100 flex justify-end">
                        <button
                            onClick={handleSaveAlerts}
                            disabled={saving || !alertConfig}
                            className="flex items-center gap-2 px-8 py-3 bg-primary text-white font-bold rounded-lg hover:bg-primary/90 transition-all shadow-md active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
                        >
                            {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
                            {saving ? "Saving Preferences..." : "Save Preferences"}
                        </button>
                    </div>
                </div>
            </section>

            {/* Profile Settings (Secondary) */}
            <section className="bg-white rounded-xl shadow-sm border border-gray-100 opacity-80">
                <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex items-center gap-3">
                    <div className="p-2 bg-gray-200 text-gray-500 rounded-lg">
                        <User size={20} />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-gray-700">Profile Information</h3>
                    </div>
                </div>
                <div className="p-6">
                    <p className="text-sm text-gray-500 italic">Profile management is currently read-only.</p>
                </div>
            </section>

            {/* Danger Zone */}
            <section className="bg-white rounded-xl shadow-sm border border-danger/20 overflow-hidden">
                <div className="p-6 border-b border-danger/10 bg-danger/5 flex items-center gap-3">
                    <div className="p-2 bg-danger/10 text-danger rounded-lg">
                        <ShieldAlert size={20} />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-danger">Danger Zone</h3>
                        <p className="text-sm text-danger/70">Irreversible actions.</p>
                    </div>
                </div>

                <div className="p-6 flex flex-col sm:flex-row items-center justify-between gap-6">
                    <div>
                        <h4 className="font-bold text-gray-800">Clear All Alert Histories</h4>
                        <p className="text-sm text-gray-500 mt-1">Resets the alert status for all datasets.</p>
                    </div>
                    <button className="flex-shrink-0 px-6 py-2.5 bg-white border-2 border-danger text-danger font-bold rounded-lg hover:bg-danger hover:text-white transition-colors">
                        Reset Status
                    </button>
                </div>
            </section>

        </div>
    );
}
