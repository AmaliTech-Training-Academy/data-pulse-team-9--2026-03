"use client";

import {
    Users,
    Database,
    Activity,
    ClipboardCheck,
    FileText,
    Clock,
    AlertTriangle,
    ArrowRight
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
    { date: "Oct 18", score: 62 },
    { date: "Oct 19", score: 68 },
    { date: "Oct 20", score: 71 },
    { date: "Oct 21", score: 68 },
    { date: "Oct 22", score: 74 },
    { date: "Oct 23", score: 78 },
    { date: "Oct 24", score: 82 },
];

const worstDatasets = [
    { id: 1, name: "legacy_users_v2.csv", user: "John Doe", score: 32, issues: 450 },
    { id: 2, name: "old_sales_data.json", user: "Smith Corp", score: 41, issues: 890 },
    { id: 3, name: "march_leads_raw.csv", user: "Marketing Team", score: 45, issues: 210 },
    { id: 4, name: "q1_returns.csv", user: "Sarah Designer", score: 48, issues: 115 },
    { id: 5, name: "test_data_dump.json", user: "Dev Team", score: 52, issues: 88 },
];

const recentActivity = [
    { id: 1, action: "Upload", user: "Sarah Designer", file: "customers_q1.csv", score: 98, time: "10 mins ago" },
    { id: 2, action: "Validation", user: "John Doe", file: "inventory.csv", score: 65, time: "1 hour ago" },
    { id: 3, action: "Rule Added", user: "Marketing Team", file: "leads.json", score: null, time: "2 hours ago" },
    { id: 4, action: "Upload", user: "Smith Corp", file: "sales_data.csv", score: 85, time: "3 hours ago" },
    { id: 5, action: "Validation", user: "Sarah Designer", file: "products.json", score: 92, time: "5 hours ago" },
];

const activeUsers = [
    { id: 1, name: "Sarah Designer", uploads: 45, avgScore: 92 },
    { id: 2, name: "Marketing Team", uploads: 38, avgScore: 85 },
    { id: 3, name: "John Doe", uploads: 24, avgScore: 68 },
    { id: 4, name: "Smith Corp", uploads: 18, avgScore: 88 },
];

const getScoreColor = (score: number | null) => {
    if (score === null) return "text-gray-500 bg-gray-100";
    if (score >= 80) return "text-success bg-success/10 border-success/20";
    if (score >= 50) return "text-warning bg-warning/10 border-warning/20";
    return "text-danger bg-danger/10 border-danger/20";
};

export default function AdminOverview() {
    return (
        <div className="space-y-6">

            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-primary">System Overview</h2>
                <p className="text-gray-500">Monitor platform health, activity, and globally uploaded datasets.</p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-md bg-blue-50 text-blue-600 flex items-center justify-center">
                            <Users size={16} />
                        </div>
                        <p className="text-xs font-bold text-gray-500 uppercase">Total Users</p>
                    </div>
                    <h3 className="text-2xl font-black text-primary">1,248</h3>
                </div>

                <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-md bg-indigo-50 text-indigo-600 flex items-center justify-center">
                            <Database size={16} />
                        </div>
                        <p className="text-xs font-bold text-gray-500 uppercase">Total Datasets</p>
                    </div>
                    <h3 className="text-2xl font-black text-primary">8,405</h3>
                </div>

                <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-md bg-success/10 text-success flex items-center justify-center">
                            <Activity size={16} />
                        </div>
                        <p className="text-xs font-bold text-gray-500 uppercase line-clamp-1">System Avg Score</p>
                    </div>
                    <h3 className="text-2xl font-black text-success">82%</h3>
                </div>

                <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-md bg-accent/10 text-accent flex items-center justify-center">
                            <ClipboardCheck size={16} />
                        </div>
                        <p className="text-xs font-bold text-gray-500 uppercase line-clamp-1">Rules Defined</p>
                    </div>
                    <h3 className="text-2xl font-black text-primary">42.5k</h3>
                </div>

                <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-md bg-purple-50 text-purple-600 flex items-center justify-center">
                            <FileText size={16} />
                        </div>
                        <p className="text-xs font-bold text-gray-500 uppercase line-clamp-1">Reports Gen.</p>
                    </div>
                    <h3 className="text-2xl font-black text-primary">12.1k</h3>
                </div>

                <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-md bg-[#0ea5e9]/10 text-[#0ea5e9] flex items-center justify-center">
                            <Clock size={16} />
                        </div>
                        <p className="text-xs font-bold text-gray-500 uppercase line-clamp-1">Last Check Run</p>
                    </div>
                    <h3 className="text-xl font-bold text-primary mt-1">10 min ago</h3>
                </div>
            </div>

            {/* Main Grid Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Left Column */}
                <div className="lg:col-span-2 space-y-6">

                    {/* System Line Chart */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h3 className="text-lg font-bold text-primary">System-Wide Quality Score</h3>
                                <p className="text-sm text-gray-500">Average dataset quality across all users</p>
                            </div>
                            <select className="bg-gray-50 border border-gray-200 text-sm rounded-lg px-3 py-2 text-gray-600 outline-none focus:ring-2 focus:ring-accent font-medium">
                                <option>Last 7 Days</option>
                                <option>Last 30 Days</option>
                                <option>This Year</option>
                            </select>
                        </div>
                        <div className="h-72 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
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
                                        stroke="#08293C"
                                        strokeWidth={3}
                                        dot={{ fill: '#08293C', strokeWidth: 2, r: 4, stroke: '#FFFFFF' }}
                                        activeDot={{ r: 6, strokeWidth: 0, fill: '#FF5A00' }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Attention Needed Table */}
                    <div className="bg-white rounded-xl shadow-sm border border-danger/20 overflow-hidden">
                        <div className="p-5 border-b border-danger/10 bg-danger/5 flex items-center justify-between">
                            <h3 className="text-lg font-bold text-danger flex items-center gap-2">
                                <AlertTriangle size={18} /> Needs Attention <span className="text-sm font-medium text-danger/70 bg-danger/10 px-2 py-0.5 rounded-full ml-1">Lowest Scores</span>
                            </h3>
                            <button className="text-sm font-medium text-danger hover:underline">View All Critical</button>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-gray-50 border-b border-gray-100">
                                        <th className="py-3 px-5 text-xs font-semibold text-gray-500 uppercase">Dataset</th>
                                        <th className="py-3 px-5 text-xs font-semibold text-gray-500 uppercase">Owner</th>
                                        <th className="py-3 px-5 text-xs font-semibold text-gray-500 uppercase">Failed Rows</th>
                                        <th className="py-3 px-5 text-xs font-semibold text-gray-500 uppercase text-right">Score</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {worstDatasets.map((dataset) => (
                                        <tr key={dataset.id} className="hover:bg-red-50/30 transition-colors">
                                            <td className="py-3 px-5 font-medium text-primary">{dataset.name}</td>
                                            <td className="py-3 px-5 text-sm text-gray-600 flex items-center gap-2">
                                                <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">{dataset.user.charAt(0)}</div>
                                                {dataset.user}
                                            </td>
                                            <td className="py-3 px-5 text-sm font-semibold text-danger">{dataset.issues.toLocaleString()}</td>
                                            <td className="py-3 px-5 text-right">
                                                <span className={`inline-flex items-center justify-center px-2.5 py-1 rounded-full text-xs font-bold border ${getScoreColor(dataset.score)}`}>
                                                    {dataset.score}%
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                </div>

                {/* Right Column */}
                <div className="lg:col-span-1 space-y-6">

                    {/* Recent Activity Feed */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100">
                        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
                            <h3 className="text-lg font-bold text-primary">Recent Activity</h3>
                        </div>
                        <div className="p-0">
                            <div className="divide-y divide-gray-100">
                                {recentActivity.map((activity) => (
                                    <div key={activity.id} className="p-4 hover:bg-gray-50 transition-colors">
                                        <div className="flex justify-between items-start mb-1">
                                            <span className="text-xs font-bold uppercase tracking-wider text-accent">{activity.action}</span>
                                            <span className="text-xs text-gray-400">{activity.time}</span>
                                        </div>
                                        <p className="text-sm text-gray-800">
                                            <span className="font-semibold">{activity.user}</span> on <span className="font-mono text-primary bg-primary/5 px-1 py-0.5 rounded">{activity.file}</span>
                                        </p>
                                        {activity.score !== null && (
                                            <div className="mt-2">
                                                <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${getScoreColor(activity.score)} border-none`}>
                                                    Score: {activity.score}%
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                            <div className="p-4 border-t border-gray-100 text-center bg-gray-50/50 rounded-b-xl">
                                <button className="text-sm font-semibold text-primary hover:text-accent transition-colors flex items-center justify-center gap-1 w-full">
                                    View Full Audit Log <ArrowRight size={16} />
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* User Summary Table */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="p-5 border-b border-gray-100">
                            <h3 className="text-lg font-bold text-primary">Top Active Users</h3>
                            <p className="text-xs text-gray-500 mt-0.5">Ranked by dataset uploads</p>
                        </div>
                        <table className="w-full text-left">
                            <tbody className="divide-y divide-gray-100">
                                {activeUsers.map((user, idx) => (
                                    <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="py-3 px-5">
                                            <div className="flex items-center gap-3">
                                                <span className="text-xs font-bold text-gray-400 w-4">{idx + 1}.</span>
                                                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary flex-shrink-0">
                                                    {user.name.charAt(0)}
                                                </div>
                                                <div>
                                                    <p className="text-sm font-semibold text-primary line-clamp-1">{user.name}</p>
                                                    <p className="text-xs text-gray-500">{user.uploads} uploads</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="py-3 px-5 text-right w-24">
                                            <span className={`inline-flex items-center justify-center px-2 py-1 rounded text-xs font-bold ${getScoreColor(user.avgScore)}`}>
                                                Avg: {user.avgScore}%
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                </div>
            </div>

        </div>
    );
}
