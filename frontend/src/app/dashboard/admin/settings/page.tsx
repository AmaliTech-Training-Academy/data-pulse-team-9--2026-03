"use client";

import { useState } from "react";
import {
    Settings,
    Bell,
    ShieldCheck,
    History,
    Save,
    Database,
    Mail,
    UserPlus,
    Search,
    Filter,
    CheckCircle2,
    AlertCircle
} from "lucide-react";

// Mock Audit Log Data
const auditLogs = [
    { id: 1, user: "Sarah Designer", action: "Dataset Upload", target: "customers_q1.csv", timestamp: "2023-10-24 14:30" },
    { id: 2, user: "Admin (System)", action: "Rule Updated", target: "Email Regex", timestamp: "2023-10-24 12:15" },
    { id: 3, user: "John Doe", action: "Validation Run", target: "sales_data.json", timestamp: "2023-10-24 10:45" },
    { id: 4, user: "Marketing Team", action: "New User Invited", target: "jane@corp.com", timestamp: "2023-10-23 16:20" },
    { id: 5, user: "Admin (System)", action: "Security Policy Change", target: "Password Length", timestamp: "2023-10-23 09:00" },
];

export default function AdminSettingsPage() {
    const [appName, setAppName] = useState("DataPulse Pro");
    const [threshold, setThreshold] = useState(80);
    const [globalAlerts, setGlobalAlerts] = useState(true);

    return (
        <div className="max-w-5xl mx-auto space-y-8 pb-12 animate-in fade-in duration-500">

            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-primary">System Settings</h2>
                <p className="text-gray-500">Configure global application parameters, notification rules, and monitor system activity.</p>
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
                            <h3 className="text-lg font-bold text-primary">General Configuration</h3>
                        </div>

                        <div className="p-6 space-y-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-gray-700">Application Name</label>
                                    <input
                                        type="text"
                                        value={appName}
                                        onChange={(e) => setAppName(e.target.value)}
                                        className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent outline-none font-medium transition-all"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-gray-700">Default Quality Threshold</label>
                                    <div className="flex items-center gap-4">
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={threshold}
                                            onChange={(e) => setThreshold(Number(e.target.value))}
                                            className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-accent"
                                        />
                                        <span className="font-black text-primary w-10">{threshold}%</span>
                                    </div>
                                </div>
                            </div>

                            <div className="pt-4 border-t border-gray-100">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h4 className="font-semibold text-gray-800">New User Default Role</h4>
                                        <p className="text-xs text-gray-500">Role assigned to self-registered users.</p>
                                    </div>
                                    <select className="px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-sm font-bold text-primary outline-none focus:ring-2 focus:ring-accent">
                                        <option>Standard User</option>
                                        <option>Data Analyst</option>
                                        <option>Guest (Read Only)</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Notification / SMTP Settings */}
                    <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="p-5 border-b border-gray-100 bg-gray-50/50 flex items-center gap-3">
                            <div className="p-2 bg-primary/10 text-primary rounded-lg">
                                <Bell size={20} />
                            </div>
                            <h3 className="text-lg font-bold text-primary">Notifications & SMTP</h3>
                        </div>

                        <div className="p-6 space-y-6">
                            <div className="flex items-center justify-between p-4 bg-accent/5 rounded-xl border border-accent/10">
                                <div className="flex items-center gap-3">
                                    <Mail className="text-accent" size={24} />
                                    <div>
                                        <h4 className="font-bold text-primary text-sm">Global Email Alerts</h4>
                                        <p className="text-xs text-gray-500">Enable automated quality reports via email.</p>
                                    </div>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" className="sr-only peer" checked={globalAlerts} onChange={() => setGlobalAlerts(!globalAlerts)} />
                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                                </label>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">SMTP Host</label>
                                    <input type="text" placeholder="smtp.amalitech.com" className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm" />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">SMTP Port</label>
                                    <input type="text" placeholder="587" className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm" />
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                                <button className="px-4 py-2 text-sm font-bold text-primary border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">Test Connection</button>
                                <button className="flex items-center gap-2 px-6 py-2 bg-primary text-white font-bold rounded-lg hover:bg-primary/90 transition-colors shadow-md">
                                    <Save size={18} /> Update SMTP
                                </button>
                            </div>
                        </div>
                    </section>

                    {/* System Audit Log */}
                    <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="p-5 border-b border-gray-100 bg-gray-50/50 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-primary/10 text-primary rounded-lg">
                                    <History size={20} />
                                </div>
                                <h3 className="text-lg font-bold text-primary">System Audit Log</h3>
                            </div>
                            <button className="text-xs font-bold text-accent hover:underline">Download Full Log (JSON)</button>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead>
                                    <tr className="bg-gray-50 border-b border-gray-200">
                                        <th className="py-3 px-6 text-[10px] font-bold text-gray-400 uppercase">Timestamp</th>
                                        <th className="py-3 px-6 text-[10px] font-bold text-gray-400 uppercase">User</th>
                                        <th className="py-3 px-6 text-[10px] font-bold text-gray-400 uppercase">Action</th>
                                        <th className="py-3 px-6 text-[10px] font-bold text-gray-400 uppercase">Resource</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {auditLogs.map((log) => (
                                        <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                                            <td className="py-3 px-6 text-xs text-gray-500 whitespace-nowrap">{log.timestamp}</td>
                                            <td className="py-3 px-6 text-xs font-bold text-primary">{log.user}</td>
                                            <td className="py-3 px-6 text-xs font-medium text-gray-700">{log.action}</td>
                                            <td className="py-3 px-6 text-xs font-mono text-gray-400 truncate max-w-[150px]">{log.target}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
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
                                    <span className="text-xs font-bold text-gray-500 uppercase">Database Connectivity</span>
                                    <span className="text-[10px] font-black bg-success/10 text-success px-2 py-0.5 rounded-full uppercase tracking-tighter">Healthy</span>
                                </div>
                                <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                    <div className="h-full bg-success w-[100%] shadow-[0_0_8px_rgba(13,159,110,0.5)]"></div>
                                </div>
                            </div>

                            <div>
                                <div className="flex justify-between items-center mb-1.5">
                                    <span className="text-xs font-bold text-gray-500 uppercase">API Node Load</span>
                                    <span className="text-[10px] font-black bg-success/10 text-success px-2 py-0.5 rounded-full uppercase tracking-tighter">Normal</span>
                                </div>
                                <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                    <div className="h-full bg-success w-[24%]"></div>
                                </div>
                            </div>

                            <div>
                                <div className="flex justify-between items-center mb-1.5">
                                    <span className="text-xs font-bold text-gray-500 uppercase">Storage Capacity</span>
                                    <span className="text-[10px] font-black bg-warning/10 text-warning px-2 py-0.5 rounded-full uppercase tracking-tighter">65% Full</span>
                                </div>
                                <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                    <div className="h-full bg-warning w-[65%]"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Quick Actions */}
                    <div className="bg-primary text-white p-6 rounded-xl shadow-xl shadow-primary/20 relative overflow-hidden group">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full -mr-16 -mt-16 group-hover:scale-125 transition-transform duration-700"></div>
                        <h4 className="font-bold mb-4 relative z-10">Admin Quick Actions</h4>
                        <div className="space-y-3 relative z-10">
                            <button className="w-full flex items-center gap-3 px-4 py-3 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-semibold transition-all">
                                <UserPlus size={18} className="text-accent" /> Invite New Admin
                            </button>
                            <button className="w-full flex items-center gap-3 px-4 py-3 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-semibold transition-all">
                                <Database size={18} className="text-accent" /> Run Maintenance Task
                            </button>
                            <button className="w-full flex items-center gap-3 px-4 py-3 bg-red-500/80 hover:bg-red-500 rounded-lg text-sm font-black transition-all">
                                <AlertCircle size={18} /> Emergency Lockout
                            </button>
                        </div>
                    </div>

                </div>

            </div>

        </div>
    );
}
