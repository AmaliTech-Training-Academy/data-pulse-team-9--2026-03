"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/services/api";

import {
    Database,
    Activity,
    ClipboardCheck,
    Clock,
    MoreVertical,
    Play,
    Eye,
    FileText
} from "lucide-react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from "recharts";

// Mock Data
const chartData = [
    { date: "Mon", score: 65 },
    { date: "Tue", score: 59 },
    { date: "Wed", score: 80 },
    { date: "Thu", score: 81 },
    { date: "Fri", score: 92 },
    { date: "Sat", score: 95 },
    { date: "Sun", score: 98 },
];

interface Dataset {
    id: number;
    dataset_id: number;
    score: number | null;
    total_rules: number | null;
    passed_rules: number | null;
    failed_rules: number | null;
    checked_at: string | null;
    name?: string; // We'll add a dummy name since the backend doesn't return file name yet
}

const getScoreColor = (score: number | null) => {
    if (score === null) return "text-gray-500 bg-gray-100";
    if (score >= 80) return "text-success bg-success/10";
    if (score >= 50) return "text-warning bg-warning/10";
    return "text-danger bg-danger/10";
};

export default function DashboardOverview() {
    const [datasets, setDatasets] = useState<Dataset[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadDashboard = async () => {
            try {
                // The API needs standard headers + auth token if available (fetchApi uses standard Next patterns)
                const options = {
                    headers: {
                        ...(localStorage.getItem("token") ? { "Authorization": `Bearer ${localStorage.getItem("token")}` } : {})
                    }
                };
                const data = await fetchApi("/reports/dashboard", options);

                // Add mock names temporarily since backend doesn't send filename yet
                const processed = data.map((d: Record<string, unknown>) => ({
                    ...d,
                    name: `dataset_file_${(d as { dataset_id: number }).dataset_id}.csv`
                }));
                setDatasets(processed);
            } catch (err) {
                console.error("Failed to load dashboard:", err);
            } finally {
                setLoading(false);
            }
        };

        loadDashboard();
    }, []);

    // Derived statistics
    const totalDatasets = datasets.length;
    const scores = datasets.filter(d => d.score !== null).map(d => d.score as number);
    const avgScore = scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;

    // For rules we can mock total sum of total_rules
    const rulesDefined = datasets.reduce((sum, d) => sum + (d.total_rules || 0), 0) || 156;

    // Latest Run
    const latestCheck = datasets
        .filter(d => d.checked_at !== null)
        .sort((a, b) => new Date(b.checked_at!).getTime() - new Date(a.checked_at!).getTime())[0]?.checked_at;

    const formattedLastCheck = latestCheck
        ? new Date(latestCheck).toLocaleDateString()
        : "No checks run";

    return (
        <div className="space-y-6">

            {/* Welcome Section */}
            <div>
                <h2 className="text-2xl font-bold text-primary">Overview</h2>
                <p className="text-gray-500">Welcome back! Here&apos;s what&apos;s happening with your data today.</p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-panel p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
                    <div className="w-12 h-12 bg-primary/10 text-primary rounded-lg flex items-center justify-center">
                        <Database size={24} />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-500">Total Datasets</p>
                        <h3 className="text-2xl font-bold text-primary">{loading ? "..." : totalDatasets}</h3>
                    </div>
                </div>

                <div className="bg-panel p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
                    <div className="w-12 h-12 bg-success/10 text-success rounded-lg flex items-center justify-center">
                        <Activity size={24} />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-500">Avg Quality Score</p>
                        <h3 className="text-2xl font-bold text-primary">{loading ? "..." : `${avgScore}%`}</h3>
                    </div>
                </div>

                <div className="bg-panel p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
                    <div className="w-12 h-12 bg-accent/10 text-accent rounded-lg flex items-center justify-center">
                        <ClipboardCheck size={24} />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-500">Rules Defined</p>
                        <h3 className="text-2xl font-bold text-primary">{loading ? "..." : rulesDefined}</h3>
                    </div>
                </div>

                <div className="bg-panel p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
                    <div className="w-12 h-12 bg-[#0ea5e9]/10 text-[#0ea5e9] rounded-lg flex items-center justify-center">
                        <Clock size={24} />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-500">Last Check Run</p>
                        <h3 className="text-lg font-bold text-primary mt-1">{loading ? "..." : formattedLastCheck}</h3>
                    </div>
                </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Left Column: Chart & Datasets */}
                <div className="lg:col-span-2 space-y-6">

                    {/* Chart Section */}
                    <div className="bg-panel p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-bold text-primary">Quality Score Trend</h3>
                            <select className="bg-gray-50 border border-gray-200 text-sm rounded-lg px-3 py-2 text-gray-600 outline-none focus:ring-2 focus:ring-accent">
                                <option>customers_q1.csv</option>
                                <option>sales_data_2023.json</option>
                            </select>
                        </div>
                        <div className="h-72 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData} margin={{ top: 5, right: 30, left: -20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                    <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} dy={10} />
                                    <YAxis axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} domain={[0, 100]} />
                                    <Tooltip
                                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                        itemStyle={{ color: '#08293C', fontWeight: 'bold' }}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="score"
                                        stroke="#FF5A00"
                                        strokeWidth={3}
                                        dot={{ fill: '#FF5A00', strokeWidth: 2, r: 4, stroke: '#FFFFFF' }}
                                        activeDot={{ r: 6, strokeWidth: 0 }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Recent Datasets Table */}
                    <div className="bg-panel rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="p-6 border-b border-gray-100 flex items-center justify-between">
                            <h3 className="text-lg font-bold text-primary">Recent Datasets</h3>
                            <button className="text-sm font-medium text-accent hover:text-orange-600 transition-colors">View All</button>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-gray-50 border-b border-gray-100">
                                        <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">File Name</th>
                                        <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Upload Date</th>
                                        <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Score</th>
                                        <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {datasets.slice(0, 5).map((dataset) => (
                                        <tr key={dataset.dataset_id || dataset.id} className="hover:bg-gray-50/50 transition-colors">
                                            <td className="py-4 px-6">
                                                <div className="flex items-center gap-3">
                                                    <FileText size={18} className="text-gray-400" />
                                                    <span className="font-medium text-gray-700">{dataset.name}</span>
                                                </div>
                                            </td>
                                            <td className="py-4 px-6 text-sm text-gray-500">
                                                {dataset.checked_at ? new Date(dataset.checked_at).toLocaleDateString() : 'N/A'}
                                            </td>
                                            <td className="py-4 px-6">
                                                {dataset.score !== null ? (
                                                    <span className={`inline-flex items-center justify-center px-2.5 py-1 rounded-full text-xs font-bold ${getScoreColor(dataset.score)}`}>
                                                        {dataset.score}%
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center justify-center px-2.5 py-1 rounded-full text-xs font-bold bg-gray-100 text-gray-500">
                                                        Pending
                                                    </span>
                                                )}
                                            </td>
                                            <td className="py-4 px-6 text-right">
                                                <div className="flex items-center justify-end gap-2">
                                                    <button className="p-1.5 text-gray-400 hover:text-accent bg-white rounded-md border border-gray-200 shadow-sm transition-colors" title="Run Check">
                                                        <Play size={16} />
                                                    </button>
                                                    <button className="p-1.5 text-gray-400 hover:text-primary bg-white rounded-md border border-gray-200 shadow-sm transition-colors" title="View Details">
                                                        <Eye size={16} />
                                                    </button>
                                                    <button className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors">
                                                        <MoreVertical size={16} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                    {datasets.length === 0 && !loading && (
                                        <tr>
                                            <td colSpan={4} className="py-8 text-center text-gray-500">No datasets found. Upload one to get started!</td>
                                        </tr>
                                    )}
                                    {loading && (
                                        <tr>
                                            <td colSpan={4} className="py-8 text-center text-gray-400">Loading datasets...</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                </div>

                {/* Right Column: Recent Reports */}
                <div className="lg:col-span-1">
                    <div className="bg-panel rounded-xl shadow-sm border border-gray-100">
                        <div className="p-6 border-b border-gray-100">
                            <h3 className="text-lg font-bold text-primary">Recent Reports</h3>
                            <p className="text-sm text-gray-500 mt-1">Latest validation check results.</p>
                        </div>
                        <div className="p-0">
                            {datasets.filter(d => d.score !== null).slice(0, 5).map((report, idx, arr) => (
                                <div
                                    key={report.id || report.dataset_id}
                                    className={`p-4 flex items-center justify-between hover:bg-gray-50 transition-colors cursor-pointer ${idx !== arr.length - 1 ? 'border-b border-gray-100' : ''
                                        }`}
                                >
                                    <div className="flex-1 min-w-0 pr-4">
                                        <p className="text-sm font-semibold text-gray-800 truncate">{report.name}</p>
                                        <p className="text-xs text-gray-500 mt-0.5">
                                            {report.checked_at ? new Date(report.checked_at).toLocaleDateString() : ""}
                                        </p>
                                    </div>
                                    <div className="flex-shrink-0">
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border-2 ${(report.score as number) >= 80 ? 'border-success text-success bg-white' :
                                            (report.score as number) >= 50 ? 'border-warning text-warning bg-white' :
                                                'border-danger text-danger bg-white'
                                            }`}>
                                            {report.score}
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {datasets.filter(d => d.score !== null).length === 0 && !loading && (
                                <div className="p-8 text-center text-sm text-gray-500">
                                    No checks run yet.
                                </div>
                            )}
                        </div>
                        <div className="p-4 border-t border-gray-100 bg-gray-50/50 rounded-b-xl">
                            <button className="w-full py-2 text-sm font-semibold text-primary hover:text-accent transition-colors">
                                View All Reports →
                            </button>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
