"use client";

import { useState, useEffect } from "react";
import {
  ChevronRight,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  Calendar,
  Search,
  User,
  Loader2,
} from "lucide-react";
import { fetchApi } from "@/services/api";
import {
  getDashboardReports,
  getDatasetReport,
  QualityReport,
} from "@/services/reports";
import { QualityScoreResponse } from "@/services/checks";

const getScoreColor = (score: number) => {
  if (score >= 80) return "text-success";
  if (score >= 50) return "text-warning";
  return "text-danger";
};

const getScoreBg = (score: number) => {
  if (score >= 80) return "bg-success";
  if (score >= 50) return "bg-warning";
  return "bg-danger";
};

interface EnrichedReport extends QualityScoreResponse {
  dataset_name: string;
  user_email: string;
}

export default function AdminReportsPage() {
  const [reports, setReports] = useState<EnrichedReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  // Detail view state
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [reportDetail, setReportDetail] = useState<QualityReport | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const token = localStorage.getItem("token");
        const options = { headers: { Authorization: `Bearer ${token}` } };

        // Fetch datasets to get names and users
        const [datasetsData, scoresData] = await Promise.all([
          fetchApi("/datasets", options),
          getDashboardReports(),
        ]);

        const datasetsArray = Array.isArray(datasetsData)
          ? datasetsData
          : datasetsData?.results || datasetsData?.datasets || [];

        // Create a lookup map for dataset details
        const datasetMap = new Map();
        datasetsArray.forEach(
          (d: {
            id: number;
            name?: string;
            file_type?: string;
            uploaded_by?: { email?: string };
          }) => {
            datasetMap.set(d.id, {
              name: d.name || `dataset_${d.id}.${d.file_type || "csv"}`,
              user: d.uploaded_by?.email || "System User",
            });
          }
        );

        // Enrich reports with dataset names and users
        const enriched = scoresData.map((score) => {
          const ds = datasetMap.get(score.dataset_id);
          return {
            ...score,
            dataset_name: ds?.name || `Dataset #${score.dataset_id}`,
            user_email: ds?.user || "Unknown",
          };
        });

        setReports(enriched);
      } catch (err) {
        console.error("Failed to load reports:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboard();
  }, []);

  const handleReportClick = async (datasetId: number) => {
    try {
      setSelectedReportId(datasetId);
      setIsDetailLoading(true);
      const detail = await getDatasetReport(datasetId);
      setReportDetail(detail);
    } catch (err) {
      console.error("Failed to fetch report detail:", err);
      alert("Failed to load report details.");
      setSelectedReportId(null);
    } finally {
      setIsDetailLoading(false);
    }
  };

  const handleBackClick = () => {
    setSelectedReportId(null);
    setReportDetail(null);
  };

  const filteredReports = reports.filter(
    (r) =>
      r.dataset_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.user_email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const renderListView = () => (
    <div className="space-y-6 animate-in fade-in zoom-in-95 duration-200">
      {/* Header & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-primary">
            Global Quality Reports
          </h2>
          <p className="text-gray-500">
            View and analyze validation results across all system datasets.
          </p>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-gray-100">
        <div className="relative w-full md:w-96 group">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-accent transition-colors">
            <Search size={18} />
          </div>
          <input
            type="text"
            placeholder="Search by dataset or user..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none transition-all text-sm"
          />
        </div>
      </div>

      {/* Reports List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="divide-y divide-gray-100">
          {isLoading ? (
            <div className="p-12 text-center">
              <Loader2
                className="animate-spin text-accent mx-auto mb-4"
                size={32}
              />
              <p className="text-gray-500">Loading quality reports...</p>
            </div>
          ) : filteredReports.length === 0 ? (
            <div className="p-12 text-center text-gray-500">
              No reports found matching your search.
            </div>
          ) : (
            filteredReports.map((report) => (
              <div
                key={report.id || report.dataset_id}
                onClick={() => handleReportClick(report.dataset_id)}
                className="p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 hover:bg-gray-50 transition-colors cursor-pointer group"
              >
                <div className="flex items-center gap-6">
                  <div
                    className={`w-16 h-16 rounded-full flex items-center justify-center text-xl font-bold border-4 ${
                      (report.score || 0) >= 80
                        ? "border-success/20 text-success bg-success/5"
                        : (report.score || 0) >= 50
                          ? "border-warning/20 text-warning bg-warning/5"
                          : "border-danger/20 text-danger bg-danger/5"
                    }`}
                  >
                    {report.score || 0}
                  </div>

                  <div>
                    <h4 className="font-bold text-primary text-lg flex items-center gap-2">
                      {report.dataset_name}
                    </h4>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1 text-sm">
                      <span className="text-gray-500 font-medium flex items-center gap-1">
                        <User size={14} /> {report.user_email}
                      </span>
                      <span className="text-gray-400">|</span>
                      <span className="text-gray-500 flex items-center gap-1">
                        <Calendar size={14} />{" "}
                        {report.checked_at
                          ? new Date(report.checked_at).toLocaleString()
                          : "Unknown"}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-xs">
                      <span className="text-gray-500 font-medium">
                        Rules:{" "}
                        <span className="text-primary">
                          {report.total_rules || 0}
                        </span>
                      </span>
                      <span className="text-success font-medium flex items-center gap-1">
                        <CheckCircle2 size={12} /> {report.passed_rules || 0}{" "}
                        Passed
                      </span>
                      <span className="text-danger font-medium flex items-center gap-1">
                        <XCircle size={12} /> {report.failed_rules || 0} Failed
                      </span>
                    </div>
                  </div>
                </div>

                <div className="hidden md:flex items-center gap-3 text-sm font-semibold text-accent opacity-0 group-hover:opacity-100 transition-opacity translate-x-4 group-hover:translate-x-0">
                  Full Details <ChevronRight size={18} />
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );

  const renderDetailView = () => {
    if (isDetailLoading) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px]">
          <Loader2 className="animate-spin text-accent mb-4" size={40} />
          <p className="text-gray-500 font-medium">Loading report details...</p>
        </div>
      );
    }

    if (!reportDetail) return null;

    // Extract and aggregate total rows from the per-rule results to display in the header
    if (reportDetail.results && reportDetail.results.length > 0) {
      // Usually, each rule checks the same number of rows. We take the max.
      // To be accurate across all rules, we sum them, or just show the rules stats.
      // The acceptance criteria mentions "per-rule breakdown table shows rows passed, rows failed".
      // For the overall summary, we'll summarize the absolute worst case or sum. Let's show total rules checked for overall to be accurate to the score.
    }

    const failedCheckResults = reportDetail.results.filter(
      (r) => r.fail_count > 0
    );
    const sampleFailedRows: {
      ruleName: string;
      reason: string;
      data: string;
    }[] = [];
    failedCheckResults.forEach((r) => {
      r.sample_rows.slice(0, 10).forEach((sample) => {
        if (sampleFailedRows.length < 10) {
          sampleFailedRows.push({
            ruleName: r.rule_name,
            reason: r.details || "Rule validation failed",
            data: JSON.stringify(sample),
          });
        }
      });
    });

    return (
      <div className="space-y-6 animate-in slide-in-from-right-8 duration-300">
        {/* Back Button & Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={handleBackClick}
              className="p-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:text-accent transition-colors shadow-sm"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h2 className="text-2xl font-bold text-primary">
                Report Investigation
              </h2>
              <p className="text-gray-500">
                {reportDetail.dataset_name} •{" "}
                {new Date(reportDetail.checked_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Score Summary */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center text-center">
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-4">
              Quality Score
            </h3>
            <div
              className={`text-6xl font-black mb-2 ${getScoreColor(reportDetail.score)}`}
            >
              {reportDetail.score}%
            </div>
            <p className="text-sm font-medium text-gray-500">
              {reportDetail.score >= 80
                ? "Healthy Dataset"
                : "Attention Required"}
            </p>
          </div>

          <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-6">
              Rules Validation Summary
            </h3>
            <div className="grid grid-cols-3 gap-6">
              <div className="space-y-1">
                <p className="text-xs font-bold text-gray-400 uppercase">
                  Total Rules
                </p>
                <p className="text-2xl font-black text-primary">
                  {reportDetail.total_rules}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-success uppercase">
                  Rules Passed
                </p>
                <p className="text-2xl font-black text-success">
                  {reportDetail.passed_rules}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-danger uppercase">
                  Rules Failed
                </p>
                <p className="text-2xl font-black text-danger">
                  {reportDetail.failed_rules}
                </p>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full h-3 bg-gray-100 rounded-full mt-8 overflow-hidden flex">
              <div
                className="h-full bg-success"
                style={{
                  width: `${(reportDetail.passed_rules / Math.max(reportDetail.total_rules, 1)) * 100}%`,
                }}
              ></div>
              <div
                className="h-full bg-danger"
                style={{
                  width: `${(reportDetail.failed_rules / Math.max(reportDetail.total_rules, 1)) * 100}%`,
                }}
              ></div>
            </div>
          </div>
        </div>

        {/* Per-Rule Breakdown */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <h3 className="text-lg font-bold text-primary">
              Per-Rule Analysis (Row Counts)
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="py-3 px-6 text-xs font-bold text-primary uppercase">
                    Rule
                  </th>
                  <th className="py-3 px-6 text-xs font-bold text-primary uppercase">
                    Rows Passed
                  </th>
                  <th className="py-3 px-6 text-xs font-bold text-primary uppercase">
                    Rows Failed
                  </th>
                  <th className="py-3 px-6 text-xs font-bold text-primary uppercase">
                    Pass Rate
                  </th>
                  <th className="py-3 px-6 text-xs font-bold text-primary uppercase w-48">
                    Visual
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {reportDetail.results.map((rule) => {
                  const total = rule.pass_count + rule.fail_count;
                  const rate =
                    total > 0 ? Math.round((rule.pass_count / total) * 100) : 0;
                  return (
                    <tr
                      key={rule.rule_id}
                      className="hover:bg-gray-50/50 transition-colors"
                    >
                      <td className="py-4 px-6 font-semibold text-primary">
                        {rule.rule_name}
                      </td>
                      <td className="py-4 px-6 text-success font-medium">
                        {rule.pass_count.toLocaleString()}
                      </td>
                      <td className="py-4 px-6 text-danger font-medium">
                        {rule.fail_count.toLocaleString()}
                      </td>
                      <td className="py-4 px-6 font-bold text-gray-700">
                        {rate}%
                      </td>
                      <td className="py-4 px-6">
                        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${getScoreBg(rate)}`}
                            style={{ width: `${rate}%` }}
                          ></div>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Failed Samples */}
        {sampleFailedRows.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-danger/20 overflow-hidden">
            <div className="p-6 border-b border-danger/10 bg-danger/5">
              <h3 className="text-lg font-bold text-danger">
                Failure Samples{" "}
                <span className="text-xs font-medium bg-danger/10 px-2 py-0.5 rounded ml-2">
                  Admin View
                </span>
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="py-3 px-6 text-xs font-bold text-gray-500 uppercase">
                      Failing Rule
                    </th>
                    <th className="py-3 px-6 text-xs font-bold text-gray-500 uppercase">
                      Reason
                    </th>
                    <th className="py-3 px-6 text-xs font-bold text-gray-500 uppercase">
                      Data Dump
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {sampleFailedRows.map((row, idx) => (
                    <tr
                      key={idx}
                      className="hover:bg-red-50/30 transition-colors"
                    >
                      <td className="py-4 px-6 text-sm font-medium text-gray-600">
                        {row.ruleName}
                      </td>
                      <td className="py-4 px-6 text-sm font-semibold text-danger">
                        {row.reason}
                      </td>
                      <td className="py-4 px-6 text-xs font-mono text-gray-500 bg-gray-50/50 break-words max-w-lg">
                        {row.data}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  return selectedReportId ? renderDetailView() : renderListView();
}
