"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchApi } from "@/services/api";
import { runCheck, QualityScoreResponse } from "@/services/checks";
import { getQualityTrends } from "@/services/reports";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  Database,
  Activity,
  Play,
  Eye,
  FileText,
  ClipboardCheck,
  Clock,
  Loader2,
  AlertCircle,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Dataset {
  id: number;
  dataset_id: number;
  dataset_name?: string;
  score: number | null;
  total_rules: number | null;
  passed_rules: number | null;
  failed_rules: number | null;
  checked_at: string | null;
}

interface TrendPoint {
  date: string;
  score: number;
}

const getScoreColor = (score: number | null) => {
  if (score === null) return "text-gray-500 bg-gray-100";
  if (score >= 80) return "text-success bg-success/10";
  if (score >= 50) return "text-warning bg-warning/10";
  return "text-danger bg-danger/10";
};

export default function DashboardOverview() {
  const router = useRouter();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningChecks, setRunningChecks] = useState<Record<number, boolean>>(
    {}
  );
  const [trendData, setTrendData] = useState<TrendPoint[]>([]);
  const [trendLoading, setTrendLoading] = useState(false);
  const [selectedTrendDataset, setSelectedTrendDataset] = useState<
    number | null
  >(null);
  const [mounted, setMounted] = useState(false);
  const REAL_DATA_START_DATE = "2026-03-09";

  useEffect(() => {
    setMounted(true);
  }, []);

  const loadDashboard = useCallback(async () => {
    try {
      const data = await fetchApi("/reports/dashboard");
      const datasetsArray = (Array.isArray(data) ? data : data?.results || []) as Dataset[];
      // Filter for real data (March 9th+) or pending datasets
      const filtered = datasetsArray.filter(
        (d) => !d.checked_at || d.checked_at >= REAL_DATA_START_DATE
      );
      setDatasets(filtered);

      // If we have datasets and haven't selected one for trends yet, pick the first one with a score
      if (data.length > 0 && !selectedTrendDataset) {
        const firstWithScore = data.find((d: Dataset) => d.score !== null);
        if (firstWithScore) {
          setSelectedTrendDataset(firstWithScore.dataset_id);
        } else {
          setSelectedTrendDataset(data[0].dataset_id);
        }
      }
    } catch (err) {
      console.error("Failed to load dashboard:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedTrendDataset]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    if (selectedTrendDataset) {
      const loadTrends = async () => {
        setTrendLoading(true);
        try {
          const data = await getQualityTrends(selectedTrendDataset, {
            start_date: REAL_DATA_START_DATE,
            limit: 10,
          });
          const results = (Array.isArray(data)
            ? data
            : (data as { results?: QualityScoreResponse[]; trends?: QualityScoreResponse[] })?.results ||
              (data as { results?: QualityScoreResponse[]; trends?: QualityScoreResponse[] })?.trends || []) as QualityScoreResponse[];
          const formatted = (Array.isArray(results) ? results : [])
            .filter(
              (r): r is QualityScoreResponse & { checked_at: string } =>
                r.checked_at !== undefined
            )
            .reverse()
            .map((r) => ({
              date: new Date(r.checked_at).toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
              }),
              score: r.score ?? 0,
            }));
          setTrendData(formatted);
        } catch (err) {
          console.error("Failed to load trends:", err);
        } finally {
          setTrendLoading(false);
        }
      };
      loadTrends();
    }
  }, [selectedTrendDataset]);

  const handleRunCheck = async (datasetId: number) => {
    setRunningChecks((prev) => ({ ...prev, [datasetId]: true }));
    try {
      await runCheck(datasetId);
      await loadDashboard(); // Reload to get updated score
    } catch (err) {
      console.error("Failed to run check:", err);
    } finally {
      setRunningChecks((prev) => ({ ...prev, [datasetId]: false }));
    }
  };

  // Derived statistics
  const totalDatasets = datasets.length;
  const scores = datasets
    .filter((d) => d.score !== null)
    .map((d) => d.score as number);
  const avgScore =
    scores.length > 0
      ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
      : 0;

  const rulesDefined = datasets.reduce(
    (sum, d) => sum + (d.total_rules || 0),
    0
  );

  const latestCheck = datasets
    .filter((d) => d.checked_at !== null && d.checked_at >= REAL_DATA_START_DATE)
    .sort(
      (a, b) =>
        new Date(b.checked_at!).getTime() - new Date(a.checked_at!).getTime()
    )[0]?.checked_at;

  const formattedLastCheck = mounted && latestCheck
    ? new Date(latestCheck).toLocaleDateString()
    : mounted ? "No checks run" : "---";

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Welcome Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-[#08293c]">OVERVIEW</h2>
          <p className="text-[12px] font-medium text-gray-400 mt-1">
            Welcome back! Here&apos;s what&apos;s happening with your data
            today.
          </p>
        </div>
        <Link
          href="/dashboard/user/upload"
          className="px-5 py-2 bg-[#ff5a00] text-white text-[12px] font-bold rounded-xl hover:shadow-lg hover:shadow-[#ff5a00]/20 transition-all text-center"
        >
          + Upload New Dataset
        </Link>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          {
            icon: Database,
            label: "Total Datasets",
            value: totalDatasets,
            color: "bg-primary/10 text-primary",
          },
          {
            icon: Activity,
            label: "Avg Quality Score",
            value: `${avgScore}%`,
            color: "bg-success/10 text-success",
          },
          {
            icon: ClipboardCheck,
            label: "Rules Defined",
            value: rulesDefined,
            color: "bg-accent/10 text-accent",
          },
          {
            icon: Clock,
            label: "Last Check Run",
            value: formattedLastCheck,
            color: "bg-primary/10 text-primary",
            isRaw: true,
          },
        ].map((card, i) => (
          <div
            key={i}
            className="bg-panel p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4 animate-in slide-in-from-bottom-4 duration-500"
            style={{ animationDelay: `${i * 100}ms` }}
          >
            <div
              className={`w-12 h-12 ${card.color} rounded-lg flex items-center justify-center`}
            >
              <card.icon size={24} />
            </div>
            <div>
              <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-0.5">
                {card.label}
              </p>
              <h3
                className={`font-black text-[#08293c] ${card.isRaw ? "text-base" : "text-xl"}`}
              >
                {loading ? (
                  <span className="animate-pulse">...</span>
                ) : (
                  card.value
                )}
              </h3>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Chart & Datasets */}
        <div className="lg:col-span-2 space-y-6">
          {/* Chart Section */}
          <div className="bg-panel p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-sm font-black text-[#08293c] uppercase tracking-widest">
                Quality Score Trend
              </h3>
              {datasets.length > 0 && (
                <select
                  className="bg-gray-50 border border-gray-200 text-sm rounded-lg px-3 py-2 text-gray-600 outline-none focus:ring-2 focus:ring-accent"
                  value={selectedTrendDataset || ""}
                  onChange={(e) =>
                    setSelectedTrendDataset(Number(e.target.value))
                  }
                >
                  {datasets.map((d) => (
                    <option key={d.dataset_id} value={d.dataset_id}>
                      {d.dataset_name || `Dataset #${d.dataset_id}`}
                    </option>
                  ))}
                </select>
              )}
            </div>
            <div className="h-72 w-full relative">
              {trendLoading && (
                <div className="absolute inset-0 bg-white/50 flex items-center justify-center z-10 backdrop-blur-[1px]">
                  <Loader2 className="animate-spin text-accent" size={32} />
                </div>
              )}
              {trendData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={trendData}
                    margin={{ top: 5, right: 30, left: -20, bottom: 5 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="#E5E7EB"
                    />
                    <XAxis
                      dataKey="date"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: "#6B7280", fontSize: 12 }}
                      dy={10}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: "#6B7280", fontSize: 12 }}
                      domain={[0, 100]}
                    />
                    <Tooltip
                      contentStyle={{
                        borderRadius: "12px",
                        border: "none",
                        boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                      }}
                      itemStyle={{ color: "#08293C", fontWeight: "bold" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="#FF5A00"
                      strokeWidth={3}
                      dot={{
                        fill: "#FF5A00",
                        strokeWidth: 2,
                        r: 4,
                        stroke: "#FFFFFF",
                      }}
                      activeDot={{ r: 6, strokeWidth: 0 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-gray-400 bg-gray-50/50 rounded-xl border border-dashed border-gray-200">
                  <Activity size={40} className="mb-2 opacity-20" />
                  <p className="text-sm font-medium">
                    No trend data yet. Run some checks!
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Recent Datasets Table */}
          <div className="bg-panel rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-sm font-black text-[#08293c] uppercase tracking-widest">
                Recent Datasets
              </h3>
              <Link
                href="/dashboard/user/datasets"
                className="text-[10px] font-black text-[#ff5a00] hover:opacity-70 transition-all uppercase tracking-widest"
              >
                View All
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    <th className="py-3 px-6 text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                      File Name
                    </th>
                    <th className="py-3 px-6 text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                      Upload Date
                    </th>
                    <th className="py-3 px-6 text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                      Quality Score
                    </th>
                    <th className="py-3 px-6 text-[10px] font-bold text-gray-400 uppercase tracking-widest text-right">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 font-medium">
                  {datasets.slice(0, 5).map((dataset) => (
                    <tr
                      key={dataset.dataset_id}
                      className="hover:bg-gray-50/50 transition-all group"
                    >
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-gray-100 text-gray-400 rounded-lg flex items-center justify-center group-hover:bg-accent/10 group-hover:text-accent transition-colors">
                            <FileText size={16} />
                          </div>
                          <span className="text-[#08293c] text-sm font-bold truncate max-w-[150px] md:max-w-[250px]">
                            {dataset.dataset_name ||
                              `Dataset #${dataset.dataset_id}`}
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-6 text-sm text-gray-500">
                        {mounted && dataset.checked_at
                          ? new Date(dataset.checked_at).toLocaleDateString()
                          : "Pending"}
                      </td>
                      <td className="py-4 px-6">
                        {dataset.score !== null ? (
                          <div className="flex items-center gap-2">
                            <div
                              className={`w-2 h-2 rounded-full ${dataset.score >= 80 ? "bg-success" : dataset.score >= 50 ? "bg-warning" : "bg-danger"}`}
                            ></div>
                            <span
                              className={`px-2 py-0.5 rounded-full text-xs font-bold ${getScoreColor(dataset.score)}`}
                            >
                              {dataset.score}%
                            </span>
                          </div>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-bold bg-gray-100 text-gray-400">
                            <Clock size={12} /> Pending
                          </span>
                        )}
                      </td>
                      <td className="py-4 px-6 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleRunCheck(dataset.dataset_id)}
                            disabled={runningChecks[dataset.dataset_id]}
                            className={`p-1.5 rounded-lg border transition-all ${
                              runningChecks[dataset.dataset_id]
                                ? "bg-gray-100 text-gray-300 border-gray-100"
                                : "bg-white text-gray-400 hover:text-accent hover:border-accent shadow-sm"
                            }`}
                            title="Run Check"
                          >
                            {runningChecks[dataset.dataset_id] ? (
                              <Loader2 size={16} className="animate-spin" />
                            ) : (
                              <Play size={16} />
                            )}
                          </button>
                          <button
                            onClick={() =>
                              router.push(
                                `/dashboard/user/reports?dataset=${dataset.dataset_id}`
                              )
                            }
                            className="p-1.5 text-gray-400 hover:text-primary bg-white rounded-lg border border-gray-200 shadow-sm transition-all"
                            title="View Details"
                          >
                            <Eye size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {datasets.length === 0 && !loading && (
                    <tr>
                      <td colSpan={4} className="py-12 text-center">
                        <div className="flex flex-col items-center text-gray-400">
                          <Database size={40} className="mb-4 opacity-20" />
                          <p className="font-semibold">No datasets found</p>
                          <Link
                            href="/dashboard/user/upload"
                            className="text-accent text-sm mt-1 hover:underline"
                          >
                            Upload your first file to begin
                          </Link>
                        </div>
                      </td>
                    </tr>
                  )}
                  {loading &&
                    Array(3)
                      .fill(0)
                      .map((_, i) => (
                        <tr key={i} className="animate-pulse">
                          <td className="py-4 px-6">
                            <div className="h-4 bg-gray-100 rounded w-48"></div>
                          </td>
                          <td className="py-4 px-6">
                            <div className="h-4 bg-gray-100 rounded w-24"></div>
                          </td>
                          <td className="py-4 px-6">
                            <div className="h-6 bg-gray-100 rounded-full w-16"></div>
                          </td>
                          <td className="py-4 px-6">
                            <div className="h-8 bg-gray-100 rounded ml-auto w-20"></div>
                          </td>
                        </tr>
                      ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Recent Reports */}
        <div className="lg:col-span-1">
          <div className="bg-panel rounded-xl shadow-sm border border-gray-100 flex flex-col h-full">
            <div className="p-6 border-b border-gray-100">
              <h3 className="text-sm font-black text-[#08293c] uppercase tracking-widest">
                Recent Activity
              </h3>
              <p className="text-[10px] font-medium text-gray-400 mt-1">
                Latest validation results
              </p>
            </div>
            <div className="flex-1 overflow-y-auto">
              {datasets
                .filter((d) => d.score !== null)
                .slice(0, 6)
                .map((report, idx, arr) => (
                  <div
                    key={report.dataset_id}
                    onClick={() =>
                      router.push(
                        `/dashboard/user/reports?dataset=${report.dataset_id}`
                      )
                    }
                    className={`p-5 flex items-center justify-between hover:bg-gray-50 transition-all cursor-pointer group ${
                      idx !== arr.length - 1 ? "border-b border-gray-100" : ""
                    }`}
                  >
                    <div className="flex-1 min-w-0 pr-4">
                      <p className="text-[13px] font-bold text-[#08293c] truncate group-hover:text-[#ff5a00] transition-colors">
                        {report.dataset_name || `Dataset #${report.dataset_id}`}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <Clock size={12} className="text-gray-400" />
                        <p className="text-[10px] font-bold text-gray-400 uppercase">
                          {report.checked_at
                            ? new Date(report.checked_at).toLocaleTimeString(
                                [],
                                { hour: "2-digit", minute: "2-digit" }
                              )
                            : ""}
                        </p>
                      </div>
                    </div>
                    <div className="flex-shrink-0">
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center text-xs font-black border-2 transition-all group-hover:scale-110 ${
                          (report.score as number) >= 80
                            ? "border-success/20 text-success bg-success/5"
                            : (report.score as number) >= 50
                              ? "border-warning/20 text-warning bg-warning/5"
                              : "border-danger/20 text-danger bg-danger/5"
                        }`}
                      >
                        {report.score}
                      </div>
                    </div>
                  </div>
                ))}
              {datasets.filter((d) => d.score !== null).length === 0 &&
                !loading && (
                  <div className="p-12 text-center flex flex-col items-center">
                    <Activity size={32} className="text-gray-200 mb-2" />
                    <p className="text-sm text-gray-400 font-medium">
                      No activity recorded
                    </p>
                  </div>
                )}
            </div>
            <Link
              href="/dashboard/user/reports"
              className="p-4 border-t border-gray-100 bg-gray-50/50 rounded-b-xl text-center text-[11px] font-black text-[#08293c] hover:text-[#ff5a00] transition-all uppercase tracking-widest"
            >
              View All Quality Reports →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
