"use client";

import { useState, useEffect, useRef } from "react";
import {
  Search,
  Filter,
  FileText,
  FileJson,
  Play,
  Eye,
  Settings,
  Loader2,
  MoreVertical,
} from "lucide-react";
import { getUsers, User } from "@/services/user";
import { getDatasets, Dataset } from "@/services/datasets";
import { runCheck } from "@/services/checks";
import Link from "next/link";
import Toast, { ToastType } from "@/components/Toast";

// Helper functions

const getStatusColor = (status: string) => {
  switch (status) {
    case "Clean":
      return "text-success";
    case "Good":
      return "text-success";
    case "Review Needed":
      return "text-warning";
    case "Critical Issues":
      return "text-danger";
    case "PROCESSING":
      return "text-gray-500 animate-pulse";
    default:
      return "text-gray-500";
  }
};

interface DatasetRow {
  id: number;
  name: string;
  user: string;
  type: string;
  date: string;
  status: string;
  score: number | null;
}

export default function AdminDatasetsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [datasets, setDatasets] = useState<DatasetRow[]>([]);
  const [usersList, setUsersList] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [checkingId, setCheckingId] = useState<number | null>(null);
  const [openDropdownId, setOpenDropdownId] = useState<number | null>(null);
  const [filterUser, setFilterUser] = useState("all");
  const [filterType, setFilterType] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [toast, setToast] = useState<{
    message: string;
    type: ToastType;
  } | null>(null);

  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setOpenDropdownId(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchDatasets = async () => {
    try {
      setIsLoading(true);
      const [allDatasets, usersData] = await Promise.all([
        getDatasets(),
        getUsers(),
      ]);

      // Reconstruct ownership by fetching datasets per user
      const userDatasetsTagged = await Promise.all(
        usersData.map(async (u) => {
          try {
            const datasets = await getDatasets(u.id);
            return {
              userId: u.id,
              userEmail: u.email,
              datasetIds: datasets.map((d: Dataset) => d.id),
            };
          } catch {
            return { userId: u.id, userEmail: u.email, datasetIds: [] };
          }
        })
      );

      const ownershipMap = new Map();
      userDatasetsTagged.forEach(({ userEmail, datasetIds }) => {
        datasetIds.forEach((id) => ownershipMap.set(id, userEmail));
      });

      const processed = allDatasets.map((d: Dataset) => {
        const userEmail = ownershipMap.get(d.id) || "System User";

        return {
          id: d.id,
          name: d.name || `dataset_file_${d.id}.${d.file_type || "csv"}`,
          user: userEmail,
          type: (d.file_type || "CSV").toUpperCase(),
          date: new Date(d.uploaded_at).toLocaleDateString(),
          status: d.status,
          score: d.score !== undefined ? d.score : null,
        };
      });

      setDatasets(processed);
      setUsersList(usersData);
    } catch (err) {
      console.error("Failed to load datasets:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleRunCheck = async (id: number) => {
    try {
      setCheckingId(id);
      await runCheck(id);
      setToast({
        message: "Quality check completed successfully!",
        type: "success",
      });
      // Refresh the list to reflect validated status
      fetchDatasets();
    } catch (err: unknown) {
      setToast({
        message:
          "Failed to run quality check: " +
          (err instanceof Error ? err.message : String(err)),
        type: "error",
      });
    } finally {
      setCheckingId(null);
    }
  };

  const filteredDatasets = datasets.filter((d) => {
    const matchesSearch =
      d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.user.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesUser = filterUser === "all" || d.user === filterUser;
    const matchesType = filterType === "all" || d.type === filterType;
    const matchesStatus =
      filterStatus === "all" ||
      (filterStatus === "checked"
        ? !["PENDING", "PROCESSING", "ERROR"].includes(d.status)
        : d.status === "PENDING");
    return matchesSearch && matchesUser && matchesType && matchesStatus;
  });

  const uniqueTypes = Array.from(new Set(datasets.map((d) => d.type)));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-primary">All System Datasets</h2>
        <p className="text-gray-500">
          Manage, validate, and moderate datasets uploaded by all registered
          users.
        </p>
      </div>

      {/* Filters & Actions Bar */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-gray-100">
        {/* Search */}
        <div className="relative w-full md:w-96 group">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-accent transition-colors">
            <Search size={18} />
          </div>
          <input
            type="text"
            placeholder="Search by file name or user email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none transition-all text-sm"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
            <Filter size={16} />
            <select
              value={filterUser}
              onChange={(e) => setFilterUser(e.target.value)}
              className="bg-transparent outline-none cursor-pointer text-gray-700 max-w-[150px]"
            >
              <option value="all">All Users</option>
              {usersList.map((u) => (
                <option key={u.id} value={u.email}>
                  {u.email}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-transparent outline-none cursor-pointer"
            >
              <option value="all">All File Types</option>
              {uniqueTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-transparent outline-none cursor-pointer"
            >
              <option value="all">Any Status</option>
              <option value="checked">Checked</option>
              <option value="unchecked">Not Checked</option>
            </select>
          </div>
        </div>
      </div>

      {/* Datasets Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[1000px]">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">
                  File Name
                </th>
                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">
                  Type
                </th>
                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">
                  Uploaded By
                </th>
                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">
                  Upload Date
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
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center">
                    <Loader2
                      className="animate-spin text-accent mx-auto mb-4"
                      size={32}
                    />
                    <p className="text-gray-500 font-medium">
                      Loading system datasets...
                    </p>
                  </td>
                </tr>
              ) : filteredDatasets.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center">
                    <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Search className="text-gray-400" size={24} />
                    </div>
                    <h3 className="text-lg font-bold text-primary mb-1">
                      No datasets found
                    </h3>
                    <p className="text-gray-500">
                      No system datasets match your criteria.
                    </p>
                  </td>
                </tr>
              ) : (
                filteredDatasets.map((dataset) => (
                  <tr
                    key={dataset.id}
                    className="hover:bg-[#F4F6F8]/50 transition-colors group"
                  >
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-3">
                        <div
                          className={`p-2 rounded-lg ${dataset.type === "CSV" ? "bg-blue-50 text-blue-600" : "bg-yellow-50 text-yellow-600"}`}
                        >
                          {dataset.type === "CSV" ? (
                            <FileText size={18} />
                          ) : (
                            <FileJson size={18} />
                          )}
                        </div>
                        <span className="font-semibold text-primary">
                          {dataset.name}
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span className="text-sm font-medium text-gray-600 border border-gray-200 bg-gray-50 px-2 py-1 rounded-md">
                        {dataset.type}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-primary/10 flex flex-shrink-0 items-center justify-center text-[10px] font-bold text-primary uppercase">
                          {dataset.user.charAt(0)}
                        </div>
                        <span className="text-sm font-medium text-gray-700 whitespace-nowrap">
                          {dataset.user}
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-sm text-gray-500">
                      {dataset.date}
                    </td>
                    <td className="py-4 px-6 text-sm font-medium">
                      <span
                        className={`flex items-center gap-1.5 ${getStatusColor(dataset.status)} whitespace-nowrap`}
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                        {dataset.status}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="relative flex justify-end">
                        <button
                          onClick={() =>
                            setOpenDropdownId(
                              openDropdownId === dataset.id ? null : dataset.id
                            )
                          }
                          className="p-2 text-gray-400 hover:text-primary rounded-lg transition-colors"
                        >
                          <MoreVertical size={20} />
                        </button>

                        {openDropdownId === dataset.id && (
                          <div
                            ref={dropdownRef}
                            className="absolute right-0 top-full mt-1 w-48 bg-white rounded-xl shadow-lg border border-gray-100 py-2 z-50 text-left"
                          >
                            {!["PROCESSING", "ERROR"].includes(
                              dataset.status
                            ) && (
                              <button
                                onClick={() => {
                                  setOpenDropdownId(null);
                                  handleRunCheck(dataset.id);
                                }}
                                disabled={checkingId === dataset.id}
                                className="w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                {checkingId === dataset.id ? (
                                  <Loader2
                                    size={16}
                                    className="animate-spin text-accent"
                                  />
                                ) : (
                                  <Play size={16} className="text-gray-400" />
                                )}
                                Run Validation
                              </button>
                            )}
                            <Link
                              href={`/dashboard/admin/datasets/${dataset.id}`}
                              className="w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3"
                            >
                              <Eye size={16} className="text-gray-400" />
                              View Details
                            </Link>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
