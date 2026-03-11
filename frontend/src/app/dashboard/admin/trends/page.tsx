"use client";

import { useEffect, useState, useMemo } from "react";
import {
    Calendar,
    Filter,
    Download,
    TrendingUp,
    Loader2
} from "lucide-react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from "recharts";
import { getDatasets, Dataset } from "@/services/datasets";
import { getBulkQualityTrends } from "@/services/reports";
import { QualityScoreResponse } from "@/services/checks";

// Colors for multiple lines
const LINE_COLORS = ["#08293C", "#FF5A00", "#0D9F6E", "#8B5CF6", "#EC4899", "#F59E0B", "#10B981"];

const getScoreColor = (score: number) => {
    if (score >= 80) return "text-success bg-success/10 border-success/20";
    if (score >= 50) return "text-warning bg-warning/10 border-warning/20";
    return "text-danger bg-danger/10 border-danger/20";
};

export default function AdminTrendsPage() {
    const [datasets, setDatasets] = useState<Dataset[]>([]);
    const [selectedDatasetIds, setSelectedDatasetIds] = useState<number[]>([]);
    const [trends, setTrends] = useState<QualityScoreResponse[]>([]);
    const [dateRange, setDateRange] = useState("30days");
    const [loading, setLoading] = useState(true);
    const [fetchingTrends, setFetchingTrends] = useState(false);

    // Initial load of datasets
    useEffect(() => {
        const loadInitialData = async () => {
            try {
                const data = await getDatasets();
                setDatasets(data);
                // Default to top 5 datasets if available for admin
                if (data.length > 0) {
                    setSelectedDatasetIds(data.slice(0, 5).map(d => d.id));
                }
            } catch (err) {
                console.error("Failed to load datasets:", err);
            } finally {
                setLoading(false);
            }
        };
        loadInitialData();
    }, []);

    // Load trends when selection or date range changes
    useEffect(() => {
        if (selectedDatasetIds.length === 0) {
            setTrends([]);
            return;
        }

        const loadTrends = async () => {
            setFetchingTrends(true);
            try {
                let start_date;
                const now = new Date();
                if (dateRange === "7days") {
                    const d = new Date();
                    d.setDate(now.getDate() - 7);
                    start_date = d.toISOString().split('T')[0];
                } else if (dateRange === "30days") {
                    const d = new Date();
                    d.setDate(now.getDate() - 30);
                    start_date = d.toISOString().split('T')[0];
                }

                const data = await getBulkQualityTrends(selectedDatasetIds, { start_date });
                setTrends(data);
            } catch (err) {
                console.error("Failed to load trends:", err);
            } finally {
                setFetchingTrends(false);
            }
        };

        loadTrends();
    }, [selectedDatasetIds, dateRange]);

    // Process data for Recharts
    const chartData = useMemo(() => {
        const dataMap: Record<string, any> = {};

        trends.forEach(t => {
            const date = t.checked_at ? new Date(t.checked_at).toLocaleDateString() : "N/A";
            if (!dataMap[date]) {
                dataMap[date] = { date };
            }
            const dataset = datasets.find(d => d.id === t.dataset_id);
            if (dataset) {
                dataMap[date][dataset.name] = t.score;
            }
        });

        return Object.values(dataMap).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    }, [trends, datasets]);

    const activeDatasets = datasets.filter(d => selectedDatasetIds.includes(d.id));

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="animate-spin text-primary" size={48} />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-primary">System-Wide Trends</h2>
                    <p className="text-gray-500">Global quality monitoring across all platform datasets.</p>
                </div>

                <div className="flex flex-col sm:flex-row items-center gap-3">
                    <div className="flex items-center gap-2 w-full sm:w-auto px-4 py-2 bg-white border border-gray-200 rounded-lg shadow-sm">
                        <Filter size={16} className="text-gray-400" />
                        <div className="text-sm font-medium text-gray-700">
                             {selectedDatasetIds.length} Datasets Active
                        </div>
                    </div>

                    <div className="flex items-center gap-2 w-full sm:w-auto px-4 py-2 bg-white border border-gray-200 rounded-lg shadow-sm">
                        <Calendar size={16} className="text-gray-400" />
                        <select
                            value={dateRange}
                            onChange={(e) => setDateRange(e.target.value)}
                            className="bg-transparent text-sm font-medium text-gray-700 outline-none w-full cursor-pointer"
                        >
                            <option value="7days">Last 7 Days</option>
                            <option value="30days">Last 30 Days</option>
                            <option value="90days">Last 90 Days</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Admin Dataset Selector */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                 <h4 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Dataset Comparison Matrix</h4>
                 <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                    {datasets.map(d => (
                        <label key={d.id} className={`flex items-center gap-2 cursor-pointer py-2 px-3 rounded-lg border transition-all ${
                            selectedDatasetIds.includes(d.id) ? 'bg-primary/5 border-primary/20' : 'bg-gray-50 border-transparent hover:border-gray-200'
                        }`}>
                            <input
                                type="checkbox"
                                checked={selectedDatasetIds.includes(d.id)}
                                onChange={(e) => {
                                    if (e.target.checked) {
                                        setSelectedDatasetIds([...selectedDatasetIds, d.id]);
                                    } else {
                                        setSelectedDatasetIds(selectedDatasetIds.filter(id => id !== d.id));
                                    }
                                }}
                                className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
                            />
                            <span className="text-xs font-semibold text-gray-700 truncate">{d.name}</span>
                        </label>
                    ))}
                 </div>
            </div>

            {/* Main Chart Card */}
            <div className="bg-white p-6 md:p-8 rounded-xl shadow-sm border border-gray-100 relative">
                {fetchingTrends && (
                    <div className="absolute inset-0 bg-white/50 backdrop-blur-[1px] flex items-center justify-center z-10 rounded-xl">
                        <Loader2 className="animate-spin text-primary" size={32} />
                    </div>
                )}
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-lg font-bold text-primary">Global Quality Performance</h3>
                    <button className="p-2 text-gray-500 hover:text-primary hover:bg-gray-50 rounded-md transition-colors border border-gray-200" title="Export Data">
                        <Download size={18} />
                    </button>
                </div>

                <div className="h-[450px] w-full">
                    {chartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                <XAxis
                                    dataKey="date"
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: '#6B7280', fontSize: 13 }}
                                    dy={15}
                                />
                                <YAxis
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: '#6B7280', fontSize: 13 }}
                                    domain={[0, 100]}
                                    dx={-10}
                                />
                                <Tooltip
                                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                    itemStyle={{ fontWeight: '600' }}
                                />
                                <Legend
                                    verticalAlign="top"
                                    height={36}
                                    iconType="rect"
                                    wrapperStyle={{ paddingBottom: '30px', fontSize: '12px', fontWeight: 'bold' }}
                                />
                                {activeDatasets.map((d, index) => (
                                    <Line
                                        key={d.id}
                                        name={d.name}
                                        type="monotone"
                                        dataKey={d.name}
                                        stroke={LINE_COLORS[index % LINE_COLORS.length]}
                                        strokeWidth={3}
                                        dot={{ fill: LINE_COLORS[index % LINE_COLORS.length], strokeWidth: 2, r: 4, stroke: '#FFFFFF' }}
                                        activeDot={{ r: 6, strokeWidth: 0, fill: '#FF5A00' }}
                                        connectNulls
                                    />
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-400">
                            <TrendingUp size={48} className="mb-4 opacity-20" />
                            <p>Select datasets to visualize global quality trends.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Historical Log */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                    <h3 className="text-lg font-bold text-primary">Comprehensive Audit Log</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-gray-50 border-b border-gray-200">
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">Timestamp</th>
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">Dataset</th>
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider text-right">Quality Score</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {trends.slice().reverse().map((record) => {
                                const dataset = datasets.find(d => d.id === record.dataset_id);
                                return (
                                    <tr key={record.id} className="hover:bg-gray-50/50 transition-colors">
                                        <td className="py-4 px-6 text-sm text-gray-500 font-medium font-mono">
                                            {record.checked_at ? new Date(record.checked_at).toLocaleString() : "N/A"}
                                        </td>
                                        <td className="py-4 px-6 font-bold text-primary">
                                            {dataset?.name || `ID: ${record.dataset_id}`}
                                        </td>
                                        <td className="py-4 px-6 text-right">
                                            <span className={`inline-flex items-center justify-center px-3 py-1 rounded-full text-xs font-black border ${getScoreColor(record.score || 0)}`}>
                                                {record.score}%
                                            </span>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
