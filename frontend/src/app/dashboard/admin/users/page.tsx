"use client";

import { useState } from "react";
import {
    Search,
    MailPlus,
    User,
    Database,
    Activity,
    MoreVertical,
    UserX,
    UserCheck,
    ChevronRight,
    ArrowLeft
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
const users = [
    { id: 1, name: "Sarah Designer", email: "sarah@amalitech.com", registered: "2023-01-15", datasetsCount: 45, avgScore: 92, lastActive: "10 mins ago", status: "Active" },
    { id: 2, name: "John Doe", email: "john@example.com", registered: "2023-02-28", datasetsCount: 24, avgScore: 68, lastActive: "1 hour ago", status: "Active" },
    { id: 3, name: "Marketing Team", email: "marketing@corp.com", registered: "2023-05-10", datasetsCount: 38, avgScore: 85, lastActive: "2 hours ago", status: "Active" },
    { id: 4, name: "Smith Corp", email: "data@smith.com", registered: "2023-06-22", datasetsCount: 18, avgScore: 88, lastActive: "1 day ago", status: "Active" },
    { id: 5, name: "Legacy System", email: "api@legacy.internal", registered: "2023-08-01", datasetsCount: 154, avgScore: 42, lastActive: "5 days ago", status: "Inactive" },
    { id: 6, name: "Test User", email: "test@amalitech.com", registered: "2023-10-01", datasetsCount: 3, avgScore: 95, lastActive: "2 weeks ago", status: "Deactivated" },
];

const mockUserDatasets = [
    { id: 1, name: "customers_q1.csv", uploadDate: "2023-10-24", score: 98 },
    { id: 2, name: "inventory_log.json", uploadDate: "2023-10-22", score: 85 },
    { id: 3, name: "sales_raw.csv", uploadDate: "2023-10-15", score: 92 },
];

const mockUserTrendData = [
    { date: "Oct 18", score: 85 },
    { date: "Oct 19", score: 88 },
    { date: "Oct 20", score: 90 },
    { date: "Oct 21", score: 85 },
    { date: "Oct 22", score: 92 },
    { date: "Oct 23", score: 96 },
    { date: "Oct 24", score: 98 },
];

const getScoreColor = (score: number) => {
    if (score >= 80) return "text-success bg-success/10 border-success/20";
    if (score >= 50) return "text-warning bg-warning/10 border-warning/20";
    return "text-danger bg-danger/10 border-danger/20";
};

export default function AdminUsersPage() {
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedUser, setSelectedUser] = useState<typeof users[0] | null>(null);

    const renderListView = () => (
        <div className="space-y-6 animate-in fade-in zoom-in-95 duration-200">

            {/* Header & Actions */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-primary">User Management</h2>
                    <p className="text-gray-500">View, invite, and moderate platform users.</p>
                </div>

                <button className="flex items-center justify-center gap-2 px-6 py-2.5 bg-accent text-white font-medium rounded-lg hover:bg-accent/90 transition-colors shadow-sm shadow-accent/20">
                    <MailPlus size={18} /> Invite New User
                </button>
            </div>

            {/* Search Bar */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center">
                <div className="relative w-full max-w-md group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-accent transition-colors">
                        <Search size={18} />
                    </div>
                    <input
                        type="text"
                        placeholder="Search by name or email address..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="block w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none transition-all text-sm"
                    />
                </div>
            </div>

            {/* Users Table */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse min-w-[1000px]">
                        <thead>
                            <tr className="bg-gray-50 border-b border-gray-200">
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">User Details</th>
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">Registration Date</th>
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider text-center">Datasets</th>
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider text-center">Avg. Score</th>
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">Last Active</th>
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">Status</th>
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {users.map((user) => (
                                <tr
                                    key={user.id}
                                    className="hover:bg-gray-50 transition-colors cursor-pointer group"
                                    onClick={() => setSelectedUser(user)}
                                >
                                    <td className="py-4 px-6">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-full bg-primary/10 flex flex-shrink-0 items-center justify-center font-bold text-primary text-sm">
                                                {user.name.charAt(0)}
                                            </div>
                                            <div>
                                                <p className="font-semibold text-primary">{user.name}</p>
                                                <p className="text-sm text-gray-500">{user.email}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="py-4 px-6 text-sm text-gray-600 font-medium">{user.registered}</td>
                                    <td className="py-4 px-6 text-center">
                                        <span className="inline-flex items-center gap-1.5 px-3 py-1 font-semibold text-primary bg-primary/5 rounded-full">
                                            <Database size={14} className="text-gray-400" /> {user.datasetsCount}
                                        </span>
                                    </td>
                                    <td className="py-4 px-6 text-center">
                                        <span className={`inline-flex items-center justify-center px-3 py-1 rounded-full text-xs font-bold border ${getScoreColor(user.avgScore)}`}>
                                            {user.avgScore}%
                                        </span>
                                    </td>
                                    <td className="py-4 px-6 text-sm text-gray-500">{user.lastActive}</td>
                                    <td className="py-4 px-6">
                                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold border ${user.status === 'Active' ? 'text-success bg-success/10 border-success/20' :
                                                user.status === 'Deactivated' ? 'text-danger bg-danger/10 border-danger/20' :
                                                    'text-gray-500 bg-gray-100 border-gray-200'
                                            }`}>
                                            <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                                            {user.status}
                                        </span>
                                    </td>
                                    <td className="py-4 px-6 text-right">
                                        <div className="flex items-center justify-end gap-3 text-sm font-semibold text-accent opacity-0 group-hover:opacity-100 transition-opacity translate-x-4 group-hover:translate-x-0">
                                            View Profile <ChevronRight size={18} />
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    );

    const renderDetailView = () => {
        if (!selectedUser) return null;

        return (
            <div className="space-y-6 animate-in slide-in-from-right-8 duration-300">

                {/* Back Button & Header Actions */}
                <div className="flex items-center justify-between">
                    <button
                        onClick={() => setSelectedUser(null)}
                        className="flex items-center gap-2 p-2 pr-4 bg-white border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 hover:text-primary transition-colors shadow-sm font-medium text-sm"
                    >
                        <ArrowLeft size={18} /> Back to Users
                    </button>

                    <div className="flex items-center gap-3">
                        {selectedUser.status === 'Active' ? (
                            <button className="flex items-center gap-2 px-4 py-2 border border-warning text-warning bg-warning/5 rounded-lg hover:bg-warning hover:text-white transition-colors text-sm font-bold shadow-sm">
                                <UserX size={16} /> Suspend User
                            </button>
                        ) : (
                            <button className="flex items-center gap-2 px-4 py-2 border border-success text-success bg-success/5 rounded-lg hover:bg-success hover:text-white transition-colors text-sm font-bold shadow-sm">
                                <UserCheck size={16} /> Reactivate
                            </button>
                        )}
                        <button className="p-2 border border-gray-200 text-gray-400 bg-white rounded-lg hover:bg-gray-50 hover:text-gray-600 transition-colors shadow-sm">
                            <MoreVertical size={20} />
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                    {/* User Profile Card */}
                    <div className="lg:col-span-1 space-y-6">
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 text-center">
                            <div className="w-24 h-24 mx-auto rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary text-4xl mb-4">
                                {selectedUser.name.charAt(0)}
                            </div>
                            <h3 className="text-xl font-bold text-primary">{selectedUser.name}</h3>
                            <p className="text-gray-500 text-sm mb-4">{selectedUser.email}</p>

                            <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border mb-6 ${selectedUser.status === 'Active' ? 'text-success bg-success/10 border-success/20' :
                                    selectedUser.status === 'Deactivated' ? 'text-danger bg-danger/10 border-danger/20' :
                                        'text-gray-500 bg-gray-100 border-gray-200'
                                }`}>
                                <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                                {selectedUser.status}
                            </div>

                            <div className="grid grid-cols-2 gap-4 border-t border-gray-100 pt-6">
                                <div>
                                    <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Registered</p>
                                    <p className="text-sm font-semibold text-primary">{selectedUser.registered}</p>
                                </div>
                                <div>
                                    <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Last Active</p>
                                    <p className="text-sm font-semibold text-primary">{selectedUser.lastActive}</p>
                                </div>
                            </div>
                        </div>

                        {/* Quick Stats Card */}
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                            <h4 className="font-bold text-primary mb-4">Performance Stats</h4>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium text-gray-500 flex items-center gap-2"><Database size={16} /> Total Datasets</span>
                                    <span className="font-bold text-primary">{selectedUser.datasetsCount}</span>
                                </div>
                                <div className="flex items-center justify-between pb-4 border-b border-gray-100">
                                    <span className="text-sm font-medium text-gray-500 flex items-center gap-2"><Activity size={16} /> Avg. Quality</span>
                                    <span className={`inline-flex items-center justify-center px-2 py-0.5 rounded text-xs font-bold border ${getScoreColor(selectedUser.avgScore)}`}>
                                        {selectedUser.avgScore}%
                                    </span>
                                </div>
                                <div>
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Overall Health</span>
                                        <span className="text-xs font-bold text-success">Excellent</span>
                                    </div>
                                    <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                                        <div className="h-full bg-success w-[92%]"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Main Content Area (Chart & Datasets) */}
                    <div className="lg:col-span-2 space-y-6">

                        {/* User Trend Chart */}
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                            <div className="flex items-center justify-between mb-6">
                                <div>
                                    <h3 className="text-lg font-bold text-primary">Quality Score Trend</h3>
                                    <p className="text-sm text-gray-500">Average dataset quality over the last 7 days.</p>
                                </div>
                            </div>
                            <div className="h-64 w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={mockUserTrendData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
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
                                            activeDot={{ r: 6, strokeWidth: 0, fill: '#08293C' }}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Datasets List */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
                                <h3 className="text-lg font-bold text-primary">Recent Uploads</h3>
                                <button className="text-sm font-semibold text-accent hover:underline">View All {selectedUser.datasetsCount}</button>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead>
                                        <tr className="bg-gray-50 border-b border-gray-100">
                                            <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Dataset Name</th>
                                            <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Upload Date</th>
                                            <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Latest Score</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {mockUserDatasets.map((dataset) => (
                                            <tr key={dataset.id} className="hover:bg-gray-50/50 transition-colors">
                                                <td className="py-4 px-6 font-medium text-primary">{dataset.name}</td>
                                                <td className="py-4 px-6 text-sm text-gray-500">{dataset.uploadDate}</td>
                                                <td className="py-4 px-6 text-right">
                                                    <span className={`inline-flex items-center justify-center px-2 py-0.5 rounded text-xs font-bold border ${getScoreColor(dataset.score)}`}>
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

                </div>

            </div>
        );
    };

    return selectedUser ? renderDetailView() : renderListView();
}
