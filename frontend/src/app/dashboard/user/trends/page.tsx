"use client";

import { useEffect, useState, useMemo } from "react";
import { Calendar, Filter, TrendingUp, Loader2 } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Area,
  AreaChart,
} from "recharts";
import { getDatasets, Dataset } from "@/services/datasets";
import { getBulkQualityTrends } from "@/services/reports";
import { getAuditLogs, AuditLogResponse } from "@/services/audit";
import { QualityScoreResponse } from "@/services/checks";
import { ChevronLeft, ChevronRight } from "lucide-react";

// Colors for multiple lines
const LINE_COLORS = [
  "#08293C",
  "#FF5A00",
  "#0D9F6E",
  "#8B5CF6",
  "#EC4899",
  "#F59E0B",
];

const getScoreColor = (score: number) => {
  if (score >= 80) return "text-success bg-success/10";
  if (score >= 50) return "text-warning bg-warning/10";
  return "text-danger bg-danger/10";
};

export default function TrendsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetIds, setSelectedDatasetIds] = useState<number[]>([]);
  const [trends, setTrends] = useState<QualityScoreResponse[]>([]);
  const [dateRange, setDateRange] = useState("30days");
  const [loading, setLoading] = useState(true);
  const [fetchingTrends, setFetchingTrends] = useState(false);
  const [mounted, setMounted] = useState(false);

  // History Audit State
  const [auditLogs, setAuditLogs] = useState<AuditLogResponse[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    setMounted(true);
  }, []);

  // Initial load of datasets
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const data = await getDatasets();
        setDatasets(data);
        // Default to top 3 datasets if available
        if (data.length > 0) {
          setSelectedDatasetIds(data.slice(0, 3).map((d) => d.id));
        }
      } catch (err) {
        console.error("Failed to load datasets:", err);
      } finally {
        setLoading(false);
      }
    };
    loadInitialData();
  }, []);

  // Real data starts on March 9th, 2026
  const REAL_DATA_START_DATE = "2026-03-09";

  // Load trends and logs when selection or date range changes
  useEffect(() => {
    if (selectedDatasetIds.length === 0) {
      setTrends([]);
      setAuditLogs([]);
      return;
    }

    const loadData = async () => {
      setFetchingTrends(true);
      try {
        let start_date = REAL_DATA_START_DATE;
        const now = new Date();

        // Date range filter (respecting the project start date)
        if (dateRange === "7days") {
          const d = new Date();
          d.setDate(now.getDate() - 7);
          const rangeStart = d.toISOString().split("T")[0];
          if (rangeStart > start_date) start_date = rangeStart;
        } else if (dateRange === "30days") {
          const d = new Date();
          d.setDate(now.getDate() - 30);
          const rangeStart = d.toISOString().split("T")[0];
          if (rangeStart > start_date) start_date = rangeStart;
        }

        // 1. Load Trends (Chart)
        const trendsData = (await getBulkQualityTrends(selectedDatasetIds, {
          start_date,
        })) as QualityScoreResponse[] | { results?: QualityScoreResponse[]; trends?: QualityScoreResponse[] };
        const trendsArray = Array.isArray(trendsData)
          ? trendsData
          : (trendsData?.results || trendsData?.trends || []);

        // Filter out any leaked mock data just in case
        const filteredTrends = (Array.isArray(trendsArray) ? trendsArray : []).filter(
          (t) => t.checked_at && t.checked_at >= REAL_DATA_START_DATE
        );
        setTrends(filteredTrends);

        // 2. Load Audit Logs (History)
        // Fetch logs for the date range
        const logsData = await getAuditLogs({ start_date });
        const allLogs = Array.isArray(logsData) ? logsData : logsData.results || [];

        // Filter for selected datasets and project start date
        const filteredLogs = allLogs.filter(
          (l) =>
            selectedDatasetIds.includes(l.dataset) &&
            l.timestamp >= REAL_DATA_START_DATE
        );

        setAuditLogs(filteredLogs);
        setCurrentPage(1); // Reset pagination on filter change
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setFetchingTrends(false);
      }
    };

    loadData();
  }, [selectedDatasetIds, dateRange]);

  // Process data for Recharts
  const chartData = useMemo(() => {
    // Map of date string -> { date, datasetId1: score1, datasetId2: score2, ... }
    const dataMap: Record<string, Record<string, string | number>> = {};

    trends.forEach((t) => {
      const date = mounted && t.checked_at
        ? new Date(t.checked_at).toLocaleDateString()
        : "N/A";
      if (!dataMap[date]) {
        dataMap[date] = { date };
      }
      const dataset = datasets.find((d) => d.id === t.dataset_id);
      if (dataset) {
        dataMap[date][dataset.name] = t.score ?? 0;
      }
    });

    return Object.values(dataMap).sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  }, [trends, datasets]);

  const stats = useMemo(() => {
    const sorted = [...(Array.isArray(auditLogs) ? auditLogs : [])].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
    const scores = trends.map(t => t.score || 0);
    return {
      avg: scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0,
      best: scores.length > 0 ? Math.max(...scores) : 0,
      total: sorted.length
    };
  }, [trends, auditLogs]);

  const activeDatasets = datasets.filter((d) =>
    selectedDatasetIds.includes(d.id)
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-primary" size={48} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Filters */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-[#08293c]">QUALITY TRENDS</h2>
          <p className="text-[12px] font-medium text-gray-400 mt-1">
            Track and compare dataset quality scores over time.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="flex items-center gap-2 w-full sm:w-auto px-4 py-2 bg-white border border-gray-200 rounded-lg shadow-sm">
            <Filter size={16} className="text-gray-400" />
            <div className="text-sm font-medium text-gray-700">
              {selectedDatasetIds.length} Datasets Selected
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

      {/* Dataset Selector (Checkboxes) */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-wrap gap-4">
        <span className="text-sm font-bold text-gray-500 uppercase flex items-center">
          Select:
        </span>
        {datasets.map((d) => (
          <label
            key={d.id}
            className="flex items-center gap-2 cursor-pointer py-1 px-3 hover:bg-gray-50 rounded-lg transition-colors"
          >
            <input
              type="checkbox"
              checked={selectedDatasetIds.includes(d.id)}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedDatasetIds([...selectedDatasetIds, d.id]);
                } else {
                  setSelectedDatasetIds(
                    selectedDatasetIds.filter((id) => id !== d.id)
                  );
                }
              }}
              className="w-4 h-4 text-accent border-gray-300 rounded focus:ring-accent"
            />
            <span className="text-sm font-medium text-gray-700">{d.name}</span>
          </label>
        ))}
      </div>

      {/* Summary Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center justify-between hover:border-success/50 transition-colors group">
          <div>
            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1 group-hover:text-success transition-colors">Average quality</p>
            <h3 className="text-3xl font-black text-[#08293c]">{stats.avg}%</h3>
          </div>
          <div className="w-12 h-12 bg-success/10 rounded-full flex items-center justify-center text-success group-hover:scale-110 transition-transform">
            <TrendingUp size={24} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center justify-between hover:border-accent/50 transition-colors group">
          <div>
            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1 group-hover:text-accent transition-colors">Best Performance</p>
            <h3 className="text-3xl font-black text-[#08293c]">{stats.best}%</h3>
          </div>
          <div className="w-12 h-12 bg-accent/10 rounded-full flex items-center justify-center text-accent group-hover:scale-110 transition-transform">
            <TrendingUp size={24} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center justify-between hover:border-primary/50 transition-colors group">
          <div>
            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1 group-hover:text-primary transition-colors">Total Checks</p>
            <h3 className="text-3xl font-black text-[#08293c]">{stats.total}</h3>
          </div>
          <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
            <Calendar size={24} />
          </div>
        </div>
      </div>

      {/* Main Chart Card */}
      <div className="bg-white p-6 md:p-8 rounded-xl shadow-sm border border-gray-100 relative">
        {fetchingTrends && (
          <div className="absolute inset-0 bg-white/50 backdrop-blur-[1px] flex items-center justify-center z-10 rounded-xl">
            <Loader2 className="animate-spin text-accent" size={32} />
          </div>
        )}
        <div className="flex items-center justify-between mb-8">
          <h3 className="text-sm font-black text-[#08293c] uppercase tracking-widest">
            Score Comparison
          </h3>
        </div>

        <div className="h-[400px] w-full">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={chartData}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  {activeDatasets.map((d, index) => (
                    <linearGradient
                      key={`gradient-${d.id}`}
                      id={`color-${d.id}`}
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="5%"
                        stopColor={LINE_COLORS[index % LINE_COLORS.length]}
                        stopOpacity={0.3}
                      />
                      <stop
                        offset="95%"
                        stopColor={LINE_COLORS[index % LINE_COLORS.length]}
                        stopOpacity={0}
                      />
                    </linearGradient>
                  ))}
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#E5E7EB"
                />
                <XAxis
                  dataKey="date"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#6B7280", fontSize: 13 }}
                  dy={15}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#6B7280", fontSize: 13 }}
                  domain={[0, 100]}
                  dx={-10}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-white p-4 rounded-xl shadow-xl border border-gray-100 animate-in fade-in zoom-in-95 duration-200">
                          <p className="text-xs font-black text-gray-400 uppercase tracking-widest mb-3 border-b border-gray-50 pb-2">
                            {label}
                          </p>
                          <div className="space-y-2">
                            {payload.map((entry, index) => (
                              <div
                                key={index}
                                className="flex items-center justify-between gap-4"
                              >
                                <div className="flex items-center gap-2">
                                  <div
                                    className="w-2 h-2 rounded-full"
                                    style={{ backgroundColor: entry.color }}
                                  />
                                  <span className="text-sm font-bold text-[#08293c]">
                                    {entry.name}:
                                  </span>
                                </div>
                                <span
                                  className="text-sm font-black"
                                  style={{ color: entry.color }}
                                >
                                  {entry.value}%
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend
                  verticalAlign="top"
                  height={36}
                  iconType="circle"
                  wrapperStyle={{
                    paddingBottom: "20px",
                    fontSize: "14px",
                    fontWeight: "500",
                  }}
                />
                {activeDatasets.map((d, index) => (
                  <Area
                    key={d.id}
                    name={d.name}
                    type="monotone"
                    dataKey={d.name}
                    stroke={LINE_COLORS[index % LINE_COLORS.length]}
                    fillOpacity={1}
                    fill={`url(#color-${d.id})`}
                    strokeWidth={3}
                    dot={{
                      fill: LINE_COLORS[index % LINE_COLORS.length],
                      strokeWidth: 2,
                      r: 4,
                      stroke: "#FFFFFF",
                    }}
                    activeDot={{ r: 6, strokeWidth: 0 }}
                    connectNulls
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <TrendingUp size={48} className="mb-4 opacity-20" />
              <p>No trend data available for the selected criteria.</p>
            </div>
          )}
        </div>
      </div>

      {/* Historical Scores Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h3 className="text-sm font-black text-[#08293c] uppercase tracking-widest">
            Score History Log
          </h3>
        </div>
        <div className="overflow-x-auto relative">
          {fetchingTrends && (
            <div className="absolute inset-0 bg-white/50 backdrop-blur-[1px] flex items-center justify-center z-10">
              <Loader2 className="animate-spin text-accent" size={24} />
            </div>
          )}
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="py-4 px-6 text-[10px] font-black text-[#08293c] uppercase tracking-widest">
                  Date & Time
                </th>
                <th className="py-4 px-6 text-[10px] font-black text-[#08293c] uppercase tracking-widest">
                  Dataset Name
                </th>
                <th className="py-4 px-6 text-[10px] font-black text-[#08293c] uppercase tracking-widest">
                  Quality Score
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {auditLogs
                .slice((currentPage - 1) * pageSize, currentPage * pageSize)
                .map((record) => {
                return (
                  <tr
                    key={record.id}
                    className="hover:bg-gray-50/50 transition-colors"
                  >
                    <td className="py-4 px-6 text-sm text-gray-600 font-medium">
                      {mounted && record.timestamp
                        ? new Date(record.timestamp).toLocaleString()
                        : "N/A"}
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex flex-col">
                        <span className="text-sm font-black text-[#08293c]">
                          {record.dataset_name || "Unknown Dataset"}
                        </span>
                        <span className="text-[10px] text-gray-400 font-medium">
                          Triggered by: {record.triggered_by} ({record.trigger_type})
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span
                        className={`inline-flex items-center justify-center px-2.5 py-1 rounded-full text-xs font-bold ${getScoreColor(record.score || 0)}`}
                      >
                        {record.score}%
                      </span>
                    </td>
                  </tr>
                );
              })}
              {auditLogs.length === 0 && !fetchingTrends && (
                <tr>
                  <td colSpan={3} className="py-8 text-center text-gray-500">
                    No historical records found for the selected datasets.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        {auditLogs.length > pageSize && (
          <div className="p-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
            <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
              Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, auditLogs.length)} of {auditLogs.length} records
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1 || fetchingTrends}
                className="p-1 rounded bg-white border border-gray-200 text-gray-400 hover:text-accent disabled:opacity-50 transition-colors"
              >
                <ChevronLeft size={16} />
              </button>
              <div className="text-xs font-bold text-[#08293c]">
                Page {currentPage} of {Math.ceil(auditLogs.length / pageSize)}
              </div>
              <button
                onClick={() => setCurrentPage(prev => Math.min(Math.ceil(auditLogs.length / pageSize), prev + 1))}
                disabled={currentPage >= Math.ceil(auditLogs.length / pageSize) || fetchingTrends}
                className="p-1 rounded bg-white border border-gray-200 text-gray-400 hover:text-accent disabled:opacity-50 transition-colors"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
