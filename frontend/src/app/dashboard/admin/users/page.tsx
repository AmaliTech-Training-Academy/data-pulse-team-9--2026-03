"use client";

import { useEffect, useState, useMemo } from "react";
import {
  Search,
  Database,
} from "lucide-react";
import { getUsers, User } from "@/services/user";
import { getDatasets, Dataset } from "@/services/datasets";
import { Loader2, Users } from "lucide-react";

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
                datasetIds: datasets.map((d: Dataset) => d.id),
              };
            } catch {
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
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {usersWithStats.length > 0 ? (
                usersWithStats.map((user) => (
                  <tr
                    key={user.id}
                    className="hover:bg-gray-50 transition-colors"
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

                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="py-20 text-center">
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

  return renderListView();
}
