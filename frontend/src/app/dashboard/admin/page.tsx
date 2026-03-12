"use client";

import {
  Users,
  Database,
  Activity,
  ClipboardCheck,
  Clock,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import { useEffect, useState, useMemo } from "react";
import { getUsers, User as UserType } from "@/services/user";
import { getDatasets, Dataset } from "@/services/datasets";
import { getRules, ValidationRule as Rule } from "@/services/rules";
import { getAuditLogs, AuditLogResponse as AuditLog } from "@/services/audit";
import { getSystemHealth, SystemHealth } from "@/services/health";
import { getBulkQualityTrends } from "@/services/reports";
import { Loader2 } from "lucide-react";

const REAL_DATA_START_DATE = "2026-03-09";

const getScoreColor = (score: number | null) => {
  if (score === null) return "text-gray-500 bg-gray-100";
  if (score >= 80) return "text-success bg-success/10 border-success/20";
  if (score >= 50) return "text-warning bg-warning/10 border-warning/20";
  return "text-danger bg-danger/10 border-danger/20";
};

export default function AdminOverview() {
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState<UserType[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [chartData, setChartData] = useState<{ date: string; score: number }[]>(
    []
  );

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [usersData, datasetsData, rulesData, auditData, healthData] =
          await Promise.all([
            getUsers(),
            getDatasets(),
            getRules(),
            getAuditLogs(),
            getSystemHealth(),
          ]);

        const filteredDatasets = datasetsData;

        setUsers(usersData);
        setDatasets(filteredDatasets);
        setRules(rulesData);

        const logs = Array.isArray(auditData) ? auditData : auditData.results;
        setAuditLogs(logs.slice(0, 5));
        setHealth(healthData);

        // Fetch trends for chart (collect all dataset IDs)
        if (filteredDatasets.length > 0) {
          const ids = filteredDatasets.map((d) => d.id);
          const trends = await getBulkQualityTrends(ids, {
            start_date: REAL_DATA_START_DATE,
          });

          if (Array.isArray(trends)) {
            // Group trends by date for a system-wide view
            const grouped = trends.reduce(
              (
                acc: Record<
                  string,
                  { date: string; score: number; count: number }
                >,
                t
              ) => {
                if (!t.checked_at) return acc;
                const date = new Date(t.checked_at).toLocaleDateString(
                  undefined,
                  {
                    month: "short",
                    day: "numeric",
                  }
                );
                if (!acc[date]) acc[date] = { date, score: 0, count: 0 };
                acc[date].score += t.score || 0;
                acc[date].count += 1;
                return acc;
              },
              {}
            );

            setChartData(
              Object.values(grouped)
                .map((g) => ({
                  date: g.date,
                  score: Math.round(g.score / g.count),
                }))
                .slice(-7)
            );
          }
        }
      } catch (err) {
        console.error("Failed to load admin dashboard:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const stats = useMemo(() => {
    const datasetsWithScores = datasets.filter(
      (d) => d.score !== undefined && d.score !== null
    );
    const avgScore =
      datasetsWithScores.length > 0
        ? Math.round(
            datasetsWithScores.reduce((acc, d) => acc + (d.score || 0), 0) /
              datasetsWithScores.length
          )
        : 0;

    const worstDatasets = datasets
      .filter((d) => d.score !== null && d.score !== undefined)
      .sort((a, b) => (a.score || 0) - (b.score || 0))
      .slice(0, 5);

    const activeUsers = users
      .map((u) => {
        const userDatasets = datasets.filter((d) => d.uploaded_by === u.id);
        const userAvgScore =
          userDatasets.length > 0
            ? Math.round(
                userDatasets.reduce((acc, d) => acc + (d.score || 0), 0) /
                  userDatasets.length
              )
            : 0;
        return {
          ...u,
          uploads: userDatasets.length,
          avgScore: userAvgScore,
        };
      })
      .sort((a, b) => b.uploads - a.uploads)
      .slice(0, 5);

    return {
      avgScore,
      worstDatasets,
      activeUsers,
      totalDatasets: datasets.length,
      totalUsers: users.length,
      totalRules: rules.length,
      totalActivity: auditLogs.length,
    };
  }, [users, datasets, rules, auditLogs]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <Loader2 className="animate-spin text-accent" size={48} />
        <p className="text-gray-500 font-medium animate-pulse">
          Calculating real-time analytics...
        </p>
      </div>
    );
  }
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Welcome Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-[#08293c]">SYSTEM OVERVIEW</h2>
          <p className="text-[12px] font-medium text-gray-400 mt-1">
            Monitor platform health, activity, and globally uploaded datasets.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div
            className={`px-5 py-2 bg-white border border-gray-100 text-[12px] font-bold rounded-xl flex items-center gap-2 ${
              health?.status === "healthy" ? "text-success" : "text-danger"
            }`}
          >
            <ShieldCheck
              size={14}
              className={
                health?.status === "healthy" ? "text-success" : "text-danger"
              }
            />
            System Status:{" "}
            {health?.status === "healthy" ? "HEALTHY" : "CRITICAL"}
          </div>
          <div className="px-5 py-2 bg-white border border-gray-100 text-[12px] font-bold text-[#08293c] rounded-xl flex items-center gap-2 text-gray-400">
            <Clock size={14} className="text-[#ff5a00]" />
            Project Since: Mar 9, 2026
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          {
            icon: Users,
            label: "Total Users",
            value: stats.totalUsers,
            color: "bg-primary/10 text-primary",
          },
          {
            icon: Database,
            label: "Total Datasets",
            value: stats.totalDatasets,
            color: "bg-indigo-50 text-indigo-600",
          },
          {
            icon: Activity,
            label: "System Avg Score",
            value: `${stats.avgScore}%`,
            color: "bg-success/10 text-success",
          },
          {
            icon: ClipboardCheck,
            label: "Rules Defined",
            value: stats.totalRules,
            color: "bg-accent/10 text-accent",
          },
        ]
          .filter(
            (card) =>
              !(card.label === "System Avg Score" && stats.avgScore === 0)
          )
          .map((card, i) => (
            <div
              key={i}
              className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4 animate-in slide-in-from-bottom-4 duration-500"
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
                <h3 className="font-black text-[#08293c] text-xl">
                  {card.value}
                </h3>
              </div>
            </div>
          ))}
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* System Line Chart */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-primary">
                  System-Wide Quality Score
                </h3>
                <p className="text-sm text-gray-500">
                  Average dataset quality across all users
                </p>
              </div>
              <select className="bg-gray-50 border border-gray-200 text-sm rounded-lg px-3 py-2 text-gray-600 outline-none focus:ring-2 focus:ring-accent font-medium">
                <option>Last 7 Days</option>
                <option>Last 30 Days</option>
                <option>This Year</option>
              </select>
            </div>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={chartData}
                  margin={{ top: 5, right: 10, left: -20, bottom: 5 }}
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
                      borderRadius: "8px",
                      border: "none",
                      boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    }}
                    itemStyle={{ color: "#08293C", fontWeight: "bold" }}
                  />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#08293C"
                    strokeWidth={3}
                    dot={{
                      fill: "#08293C",
                      strokeWidth: 2,
                      r: 4,
                      stroke: "#FFFFFF",
                    }}
                    activeDot={{ r: 6, strokeWidth: 0, fill: "#FF5A00" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Attention Needed Table */}
          <div className="bg-white rounded-xl shadow-sm border border-danger/20 overflow-hidden">
            <div className="p-5 border-b border-danger/10 bg-danger/5 flex items-center justify-between">
              <h3 className="text-lg font-bold text-danger flex items-center gap-2">
                <AlertTriangle size={18} /> Needs Attention{" "}
                <span className="text-sm font-medium text-danger/70 bg-danger/10 px-2 py-0.5 rounded-full ml-1">
                  Lowest Scores
                </span>
              </h3>
              <button className="text-sm font-medium text-danger hover:underline">
                View All Critical
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    <th className="py-3 px-5 text-xs font-semibold text-gray-500 uppercase">
                      Dataset
                    </th>
                    <th className="py-3 px-5 text-xs font-semibold text-gray-500 uppercase">
                      Owner
                    </th>
                    <th className="py-3 px-5 text-xs font-semibold text-gray-500 uppercase">
                      Failed Rows
                    </th>
                    <th className="py-3 px-5 text-xs font-semibold text-gray-500 uppercase text-right">
                      Score
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {stats.worstDatasets.length > 0 ? (
                    stats.worstDatasets.map((dataset) => (
                      <tr
                        key={dataset.id}
                        className="hover:bg-red-50/30 transition-colors"
                      >
                        <td className="py-3 px-5 font-medium text-primary">
                          {dataset.name}
                        </td>
                        <td className="py-3 px-5 text-sm text-gray-600 flex items-center gap-2">
                          <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">
                            {users
                              .find((u) => u.id === dataset.uploaded_by)
                              ?.full_name?.charAt(0) || "U"}
                          </div>
                          {users.find((u) => u.id === dataset.uploaded_by)
                            ?.full_name || "Unknown"}
                        </td>
                        <td className="py-3 px-5 text-sm font-semibold text-danger">
                          {dataset.failed_rules || 0} rules failed
                        </td>
                        <td className="py-3 px-5 text-right">
                          <span
                            className={`inline-flex items-center justify-center px-2.5 py-1 rounded-full text-xs font-bold border ${getScoreColor(dataset.score ?? null)}`}
                          >
                            {dataset.score}%
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan={4}
                        className="py-12 text-center text-gray-400 italic"
                      >
                        System is healthy - No critical failures detected since
                        Mar 9th.
                      </td>
                    </tr>
                  )}
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
              <h3 className="text-lg font-bold text-primary">
                Recent Activity
              </h3>
            </div>
            <div className="p-0">
              <div className="divide-y divide-gray-100">
                {auditLogs.map((activity) => (
                  <div
                    key={activity.id}
                    className="p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-xs font-bold uppercase tracking-wider text-accent">
                        {activity.trigger_type}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(activity.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                    <p className="text-sm text-gray-800">
                      <span className="font-semibold">
                        {activity.triggered_by}
                      </span>{" "}
                      on{" "}
                      <span className="font-mono text-primary bg-primary/5 px-1 py-0.5 rounded">
                        {activity.dataset_name}
                      </span>
                    </p>
                    {activity.score !== null && (
                      <div className="mt-2">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${getScoreColor(activity.score)} border-none`}
                        >
                          Score: {activity.score}%
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div className="p-4 border-t border-gray-100 text-center bg-gray-50/50 rounded-b-xl">
                <Link
                  href="/dashboard/admin/trends"
                  className="text-sm font-semibold text-primary hover:text-accent transition-colors flex items-center justify-center gap-1 w-full"
                >
                  View Full Audit Log <ArrowRight size={16} />
                </Link>
              </div>
            </div>
          </div>

          {/* User Summary Table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-5 border-b border-gray-100">
              <h3 className="text-lg font-bold text-primary">
                Top Active Users
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">
                Ranked by dataset uploads
              </p>
            </div>
            <table className="w-full text-left">
              <tbody className="divide-y divide-gray-100">
                {stats.activeUsers.map((user, idx) => (
                  <tr
                    key={user.id}
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td className="py-3 px-5">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-gray-400 w-4">
                          {idx + 1}.
                        </span>
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary flex-shrink-0">
                          {user.full_name?.charAt(0) || "U"}
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-primary line-clamp-1">
                            {user.full_name || user.email}
                          </p>
                          <p className="text-xs text-gray-500">
                            {user.uploads} uploads
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-5 text-right w-24">
                      <span
                        className={`inline-flex items-center justify-center px-2 py-1 rounded text-xs font-bold ${getScoreColor(user.avgScore)}`}
                      >
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
