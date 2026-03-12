"use client";

import { useEffect, useState } from "react";
import {
  Settings,
  ShieldCheck,
  AlertCircle,
  Database, // Kept for potential future use or if it's used elsewhere not shown in diff
} from "lucide-react";
import { getSystemHealth, SystemHealth } from "@/services/health";

// Health polling interval removed if it were unused, but it is used.
// System health monitoring remains.

export default function AdminSettingsPage() {
  const [appName, setAppName] = useState("DataPulse Pro");
  const [threshold, setThreshold] = useState(80);
  const [globalAlerts, setGlobalAlerts] = useState(true);
  const [health, setHealth] = useState<SystemHealth | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      const data = await getSystemHealth();
      setHealth(data);
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

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
          {/* General Settings */}
          <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-5 border-b border-gray-100 bg-gray-50/50 flex items-center gap-3">
              <div className="p-2 bg-primary/10 text-primary rounded-lg">
                <Settings size={20} />
              </div>
              <h3 className="text-lg font-bold text-primary">
                General Configuration
              </h3>
            </div>

            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-bold text-gray-700">
                    Application Name
                  </label>
                  <input
                    type="text"
                    value={appName}
                    onChange={(e) => setAppName(e.target.value)}
                    className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent outline-none font-medium transition-all"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-bold text-gray-700">
                    Default Quality Threshold
                  </label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={threshold}
                      onChange={(e) => setThreshold(Number(e.target.value))}
                      className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-accent"
                    />
                    <span className="font-black text-primary w-10">
                      {threshold}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Notification / SMTP Settings */}
          <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-5 border-b border-gray-100 bg-gray-50/50 flex items-center gap-3">
              <div className="p-2 bg-primary/10 text-primary rounded-lg">
                <Database size={20} />{" "}
                {/* Re-using Database icon for notifications */}
              </div>
              <h3 className="text-lg font-bold text-primary">
                Notifications & SMTP
              </h3>
            </div>

            <div className="p-6 space-y-6">
              <div className="flex items-center justify-between p-4 bg-accent/5 rounded-xl border border-accent/10">
                <div className="flex items-center gap-3">
                  <AlertCircle className="text-accent" size={24} />
                  <div>
                    <h4 className="font-bold text-primary text-sm">
                      Global Email Alerts
                    </h4>
                    <p className="text-xs text-gray-500">
                      Enable automated quality reports via email.
                    </p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={globalAlerts}
                    onChange={() => setGlobalAlerts(!globalAlerts)}
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                </label>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                    SMTP Host
                  </label>
                  <input
                    type="text"
                    placeholder="smtp.amalitech.com"
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                    SMTP Port
                  </label>
                  <input
                    type="text"
                    placeholder="587"
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                <button className="px-4 py-2 text-sm font-bold text-primary border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  Test Connection
                </button>
                <button className="flex items-center gap-2 px-6 py-2 bg-primary text-white font-bold rounded-lg hover:bg-primary/90 transition-colors shadow-md">
                  <Database size={18} /> Update SMTP
                </button>
              </div>
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
