"use client";

import { useEffect, useState, useMemo } from "react";
import {
  Search,
  Database,
  Activity,
  MoreVertical,
  UserX,
  UserCheck,
  ChevronRight,
  ArrowLeft,
  Users,
} from "lucide-react";
import { getUsers, User } from "@/services/user";
import { getDatasets, Dataset } from "@/services/datasets";
import { getBulkQualityTrends } from "@/services/reports";
import { Loader2 } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const REAL_DATA_START_DATE = "2026-03-09";

const getScoreColor = (score: number | null) => {
  if (score === null || score === undefined) return "text-gray-500 bg-gray-100";
  if (score >= 80) return "text-success bg-success/10 border-success/20";
  if (score >= 50) return "text-warning bg-warning/10 border-warning/20";
  return "text-danger bg-danger/10 border-danger/20";
};

interface EnrichedUser extends User {
  name: string;
  datasetsCount: number;
  avgScore: number;
  lastActive: string;
  status: string;
  recentUploads: Dataset[];
}

export default function AdminUsersPage() {
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState<User[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedUser, setSelectedUser] = useState<EnrichedUser | null>(null);
  const [userTrendData, setUserTrendData] = useState<
    { date: string; score: number }[]
  >([]);
  const [trendLoading, setTrendLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [usersData, allDatasets] = await Promise.all([
          getUsers(),
          getDatasets(),
        ]);

        // Reconstruct ownership by fetching datasets per user since backend serializer is missing uploaded_by
        const userDatasetsTagged = await Promise.all(
          usersData.map(async (u) => {
            try {
              const datasets = await getDatasets(u.id);
              return {
                userId: u.id,
                datasetIds: datasets.map((d: any) => d.id),
              };
            } catch (err) {
              return { userId: u.id, datasetIds: [] };
            }
          })
        );

        const ownershipMap = new Map();
        userDatasetsTagged.forEach(({ userId, datasetIds }) => {
          datasetIds.forEach((id) => ownershipMap.set(id, userId));
        });

        const enrichedDatasets = allDatasets.map((d: Dataset) => ({
          ...d,
          uploaded_by: ownershipMap.get(d.id),
        }));

        setUsers(usersData);
        setDatasets(enrichedDatasets);
      } catch (err) {
        console.error("Failed to load user management data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const usersWithStats = useMemo(() => {
    return users
      .map((u: User) => {
        const userDatasets = datasets.filter((d: Dataset) => {
          const uploadedBy = d.uploaded_by;
          if (typeof uploadedBy === "number") {
            return uploadedBy === u.id;
          }
          if (
            uploadedBy &&
            typeof uploadedBy === "object" &&
            "id" in uploadedBy
          ) {
            return uploadedBy.id === u.id;
          }
          return false;
        });
        const datasetsWithScores = userDatasets.filter(
          (d: Dataset) => d.score !== null && d.score !== undefined
        );
        const avgScore =
          datasetsWithScores.length > 0
            ? Math.round(
                datasetsWithScores.reduce(
                  (acc: number, d: Dataset) => acc + (d.score || 0),
                  0
                ) / datasetsWithScores.length
              )
            : 0;

        return {
          ...u,
          name: u.full_name || u.email.split("@")[0],
          datasetsCount: userDatasets.length,
          avgScore,
          lastActive: userDatasets.length > 0 ? "Recently" : "Never",
          status: "Active", // Logic for active/inactive could be added based on last uploaded_at
          recentUploads: userDatasets
            .sort(
              (a: Dataset, b: Dataset) =>
                new Date(b.uploaded_at).getTime() -
                new Date(a.uploaded_at).getTime()
            )
            .slice(0, 5),
        };
      })
      .filter(
        (u: EnrichedUser) =>
          u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          u.email.toLowerCase().includes(searchTerm.toLowerCase())
      );
  }, [users, datasets, searchTerm]);

  // Load trends for selected user
  useEffect(() => {
    if (selectedUser) {
      const loadUserTrends = async () => {
        setTrendLoading(true);
        try {
          const userDatasets = datasets.filter((d: Dataset) => {
            const uploadedBy = d.uploaded_by;
            if (
              uploadedBy &&
              typeof uploadedBy === "object" &&
              "id" in uploadedBy
            ) {
              return uploadedBy.id === selectedUser.id;
            }
            return false;
          });
          if (userDatasets.length > 0) {
            const ids = userDatasets.map((d: Dataset) => d.id);
            const trends = await getBulkQualityTrends(ids, {
              start_date: REAL_DATA_START_DATE,
            });

            if (Array.isArray(trends)) {
              const initialAcc: Record<
                string,
                { date: string; score: number; count: number }
              > = {};
              const grouped = trends.reduce((acc, t) => {
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
              }, initialAcc);

              setUserTrendData(
                Object.values(grouped)
                  .map((g: { date: string; score: number; count: number }) => ({
                    date: g.date,
                    score: Math.round(g.score / g.count),
                  }))
                  .slice(-7)
              );
            }
          } else {
            setUserTrendData([]);
          }
        } catch (err) {
          console.error("Failed to fetch user trends:", err);
        } finally {
          setTrendLoading(false);
        }
      };
      loadUserTrends();
    }
  }, [selectedUser, datasets]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <Loader2 className="animate-spin text-accent" size={48} />
        <p className="text-gray-500 font-medium">Loading user profiles...</p>
      </div>
    );
  }

  const renderListView = () => (
    <div className="space-y-6 animate-in fade-in zoom-in-95 duration-200">
      {/* Header & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-primary">User Management</h2>
          <p className="text-gray-500">View and moderate platform users.</p>
        </div>
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
                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">
                  User Details
                </th>
                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">
                  Registration Date
                </th>
                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider text-center">
                  Datasets
                </th>
                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">
                  Status
                </th>
                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider text-right">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {usersWithStats.length > 0 ? (
                usersWithStats.map((user) => (
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
                          <p className="font-semibold text-primary">
                            {user.name}
                          </p>
                          <p className="text-sm text-gray-500">{user.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-sm text-gray-600 font-medium">
                      {user.created_at
                        ? new Date(user.created_at).toLocaleDateString()
                        : "N/A"}
                    </td>
                    <td className="py-4 px-6 text-center">
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 font-semibold text-primary bg-primary/5 rounded-full">
                        <Database size={14} className="text-gray-400" />{" "}
                        {user.datasetsCount}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold border ${
                          user.status === "Active"
                            ? "text-success bg-success/10 border-success/20"
                            : "text-gray-500 bg-gray-100 border-gray-200"
                        }`}
                      >
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
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-20 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Users size={48} className="text-gray-200" />
                      <p className="text-gray-500 font-medium">
                        No active researchers found.
                      </p>
                      <p className="text-xs text-gray-400">
                        Try inviting a new user or adjusting your search
                        filters.
                      </p>
                    </div>
                  </td>
                </tr>
              )}
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
            {selectedUser.status === "Active" ? (
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
              <h3 className="text-xl font-bold text-primary">
                {selectedUser.name}
              </h3>
              <p className="text-gray-500 text-sm mb-4">{selectedUser.email}</p>

              <div
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
                  selectedUser.status === "Active"
                    ? "text-success bg-success/10 border-success/20"
                    : selectedUser.status === "Deactivated"
                      ? "text-danger bg-danger/10 border-danger/20"
                      : "text-gray-500 bg-gray-100 border-gray-200"
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                {selectedUser.status}
              </div>

              <div className="grid grid-cols-1 gap-4 border-t border-gray-100 pt-6">
                <div>
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">
                    Registered
                  </p>
                  <p className="text-sm font-semibold text-primary">
                    {selectedUser.created_at
                      ? new Date(selectedUser.created_at).toLocaleDateString()
                      : "N/A"}
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Stats Card */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <h4 className="font-bold text-primary mb-4">Performance Stats</h4>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-500 flex items-center gap-2">
                    <Database size={16} /> Total Datasets
                  </span>
                  <span className="font-bold text-primary">
                    {selectedUser.datasetsCount}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-500 flex items-center gap-2">
                    <Activity size={16} /> Avg. Quality
                  </span>
                  <span
                    className={`inline-flex items-center justify-center px-2 py-0.5 rounded text-xs font-bold border ${getScoreColor(selectedUser.avgScore)}`}
                  >
                    {selectedUser.avgScore}%
                  </span>
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
                  <h3 className="text-lg font-bold text-primary">
                    Quality Score Trend
                  </h3>
                  <p className="text-sm text-gray-500">
                    Average dataset quality over the last 7 days.
                  </p>
                </div>
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  {trendLoading ? (
                    <div className="flex items-center justify-center h-full">
                      <Loader2 className="animate-spin text-accent" size={32} />
                    </div>
                  ) : userTrendData.length > 0 ? (
                    <LineChart
                      data={userTrendData}
                      margin={{ top: 5, right: 10, left: -20, bottom: 0 }}
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
                        stroke="#FF5A00"
                        strokeWidth={3}
                        dot={{
                          fill: "#FF5A00",
                          strokeWidth: 2,
                          r: 4,
                          stroke: "#FFFFFF",
                        }}
                        activeDot={{ r: 6, strokeWidth: 0, fill: "#08293C" }}
                      />
                    </LineChart>
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                      No trend data available for this period.
                    </div>
                  )}
                </ResponsiveContainer>
              </div>
            </div>

            {/* Datasets List */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="p-6 border-b border-gray-100 flex items-center justify-between">
                <h3 className="text-lg font-bold text-primary">
                  Recent Uploads
                </h3>
                <button className="text-sm font-semibold text-accent hover:underline">
                  View All {selectedUser.datasetsCount}
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-100">
                      <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Dataset Name
                      </th>
                      <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Upload Date
                      </th>
                      <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">
                        Latest Score
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {selectedUser.recentUploads.map((dataset: Dataset) => (
                      <tr
                        key={dataset.id}
                        className="hover:bg-gray-50/50 transition-colors"
                      >
                        <td className="py-4 px-6 font-medium text-primary">
                          {dataset.name}
                        </td>
                        <td className="py-4 px-6 text-sm text-gray-500">
                          {new Date(dataset.uploaded_at).toLocaleDateString()}
                        </td>
                        <td className="py-4 px-6 text-right">
                          <span
                            className={`inline-flex items-center justify-center px-2 py-0.5 rounded text-xs font-bold border ${getScoreColor(dataset.score ?? null)}`}
                          >
                            {dataset.score}%
                          </span>
                        </td>
                      </tr>
                    ))}
                    {selectedUser.recentUploads.length === 0 && (
                      <tr>
                        <td
                          colSpan={3}
                          className="py-8 text-center text-gray-400 text-sm"
                        >
                          No real data uploads found since Mar 9th.
                        </td>
                      </tr>
                    )}
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
