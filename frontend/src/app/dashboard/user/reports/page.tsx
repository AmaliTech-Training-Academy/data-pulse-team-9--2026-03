"use client";

import { useState, useEffect } from "react";
import {
  FileText,
  ChevronRight,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  Download,
  Calendar,
  Loader2,
} from "lucide-react";

import { fetchApi } from "@/services/api";
import {
  getDashboardReports,
  getDatasetReport,
  QualityReport,
} from "@/services/reports";
import { QualityScoreResponse, getCheckResults } from "@/services/checks";

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

interface DatasetOption {
  id: number;
  name: string;
}

interface EnrichedReport extends QualityScoreResponse {
  dataset_name: string;
}

export default function ReportsPage() {
  const [datasets, setDatasets] = useState<DatasetOption[]>([]);
  const [selectedDatasetParam, setSelectedDatasetParam] =
    useState<string>("all");

  const [reports, setReports] = useState<EnrichedReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [reportDetail, setReportDetail] = useState<QualityReport | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const token = localStorage.getItem("token");
        const options = { headers: { Authorization: `Bearer ${token}` } };

        const [datasetsData, scoresData] = await Promise.all([
          fetchApi("/datasets", options),
          getDashboardReports(),
        ]);

        const datasetsArray = Array.isArray(datasetsData)
          ? datasetsData
          : datasetsData?.results || datasetsData?.datasets || [];

        const mappedDatasets = datasetsArray.map(
          (d: { id: number; name?: string; file_type?: string }) => ({
            id: d.id,
            name: d.name || `dataset_${d.id}.${d.file_type || "csv"}`,
          })
        );
        setDatasets(mappedDatasets);

        const datasetMap = new Map();
        mappedDatasets.forEach((d: DatasetOption) => {
          datasetMap.set(d.id, d.name);
        });

        const enriched = scoresData.map((score: QualityScoreResponse) => ({
          ...score,
          dataset_name:
            datasetMap.get(score.dataset_id) || `Dataset #${score.dataset_id}`,
        }));

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

      // Fetch both the report summary and the detailed check results
      const [detail, results] = await Promise.all([
        getDatasetReport(datasetId),
        getCheckResults(datasetId),
      ]);

      // If the report detail doesn't have results (backend limitation),
      // we merge the raw results from the checks endpoint.
      const mergedDetail = {
        ...detail,
        results:
          detail.results && detail.results.length > 0
            ? detail.results
            : results.map((r) => ({
                ...r,
                // Ensure field naming matches what the table expects
                pass_count: r.pass_count,
                fail_count: r.fail_count,
              })),
      };

      setReportDetail(mergedDetail);
    } catch (err) {
      console.error("Failed to fetch report detail:", err);
      // Fallback: If one fails, try to show whatever we can
      try {
        const detail = await getDatasetReport(datasetId);
        setReportDetail(detail);
      } catch (innerErr) {
        alert("Failed to load report details.");
        setSelectedReportId(null);
      }
    } finally {
      setIsDetailLoading(false);
    }
  };

  const filteredReports =
    selectedDatasetParam === "all"
      ? reports
      : reports.filter((r) => r.dataset_id.toString() === selectedDatasetParam);

  const renderListView = () => (
    <div className="space-y-6 animate-in fade-in zoom-in-95 duration-200">
      {/* Header & Dataset Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-[#08293c]">QUALITY REPORTS</h2>
          <p className="text-[12px] font-medium text-gray-400 mt-1">
            View validation results and detailed rule breakdowns.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-gray-600">Dataset:</span>
          <select
            value={selectedDatasetParam}
            onChange={(e) => setSelectedDatasetParam(e.target.value)}
            className="bg-white border border-gray-200 text-primary font-medium rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-accent min-w-[200px] shadow-sm"
          >
            <option value="all">All Datasets</option>
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Reports List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100 bg-gray-50 flex items-center gap-2">
          <FileText size={20} className="text-accent" />
          <h3 className="text-sm font-black text-[#08293c] uppercase tracking-widest leading-none">
            Report History:{" "}
            <span className="text-gray-400 font-bold ml-1">
              {selectedDatasetParam === "all"
                ? "All Datasets"
                : datasets.find((d) => d.id.toString() === selectedDatasetParam)
                    ?.name || "Unknown"}
            </span>
          </h3>
        </div>

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
              No reports available. Try running a validation check on your
              datasets.
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
                    <h4 className="text-base font-black text-[#08293c] group-hover:text-[#ff5a00] transition-colors">
                      {report.dataset_name}
                    </h4>
                    <div className="flex items-center gap-4 mt-2 text-sm">
                      <span className="text-gray-500 flex items-center gap-1">
                        <Calendar size={14} className="text-gray-400" />{" "}
                        {report.checked_at
                          ? new Date(report.checked_at).toLocaleString()
                          : "Unknown"}
                      </span>
                      <span className="text-gray-400 font-bold ml-2 text-[11px] uppercase tracking-widest">
                        Rules:{" "}
                        <span className="text-[#08293c]">
                          {report.total_rules || 0}
                        </span>
                      </span>
                      <span className="text-success font-medium flex items-center gap-1">
                        <CheckCircle2 size={14} /> {report.passed_rules || 0}{" "}
                        Passed
                      </span>
                      <span className="text-danger font-medium flex items-center gap-1">
                        <XCircle size={14} /> {report.failed_rules || 0} Failed
                      </span>
                    </div>
                  </div>
                </div>

                <div className="hidden md:flex items-center gap-3 text-sm font-semibold text-accent opacity-0 group-hover:opacity-100 transition-opacity translate-x-4 group-hover:translate-x-0">
                  View Details <ChevronRight size={18} />
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
              onClick={() => {
                setSelectedReportId(null);
                setReportDetail(null);
              }}
              className="p-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:text-accent transition-colors shadow-sm"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h2 className="text-xl font-black text-[#08293c] uppercase tracking-widest">
                Report Details
              </h2>
              <p className="text-gray-500">
                {reportDetail.dataset_name} •{" "}
                {new Date(reportDetail.checked_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Overall Score Card */}
        <div className="bg-white p-6 md:p-8 rounded-xl shadow-sm border border-gray-100 flex flex-col md:flex-row items-center gap-8">
          <div className="text-center md:text-left flex-1 w-full">
            <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-2">
              Overall Quality Score
            </h3>
            <div className="flex flex-col md:flex-row md:items-end gap-4">
              <span
                className={`text-6xl font-black ${getScoreColor(reportDetail.score)}`}
              >
                {reportDetail.score}%
              </span>
              <div className="flex items-center justify-center md:justify-start gap-6 text-sm pb-1">
                <span className="font-medium text-gray-600">
                  Total Rules: {reportDetail.total_rules}
                </span>
                <span className="font-medium text-success">
                  {reportDetail.passed_rules} Passed
                </span>
                <span className="font-medium text-danger">
                  {reportDetail.failed_rules} Failed
                </span>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full h-3 bg-gray-100 rounded-full mt-6 overflow-hidden flex">
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
            <h3 className="text-sm font-black text-[#08293c] uppercase tracking-widest">
              Per-Rule Analysis
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="py-3 px-6 text-[10px] font-black text-[#08293c] uppercase tracking-widest">
                    Rule Name
                  </th>
                  <th className="py-3 px-6 text-[10px] font-black text-[#08293c] uppercase tracking-widest">
                    Passed
                  </th>
                  <th className="py-3 px-6 text-[10px] font-black text-[#08293c] uppercase tracking-widest">
                    Failed
                  </th>
                  <th className="py-3 px-6 text-[10px] font-black text-[#08293c] uppercase tracking-widest">
                    Pass Rate
                  </th>
                  <th className="py-3 px-6 text-[10px] font-black text-[#08293c] uppercase tracking-widest w-48">
                    Progress
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
                      <td className="py-4 px-6 flex items-center">
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

        {/* Failed Rows Sample */}
        {sampleFailedRows.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-danger/20 overflow-hidden">
            <div className="p-6 border-b border-danger/10 bg-danger/5">
              <h3 className="text-lg font-bold text-danger flex items-center gap-2">
                Failed Data Samples{" "}
                <span className="text-sm font-medium text-danger/70 bg-danger/10 px-2 py-0.5 rounded-full ml-2">
                  Preview (First 10)
                </span>
              </h3>
            </div>
            <div className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50">
                      <th className="py-3 px-6 text-xs font-bold text-gray-500 uppercase">
                        Failing Rule
                      </th>
                      <th className="py-3 px-6 text-xs font-bold text-gray-500 uppercase">
                        Failure Reason
                      </th>
                      <th className="py-3 px-6 text-xs font-bold text-gray-500 uppercase">
                        Row Data Preview
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
                        <td className="py-4 px-6 text-xs font-mono text-gray-600 bg-gray-50/50 break-words max-w-lg">
                          {row.data}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return selectedReportId ? renderDetailView() : renderListView();
}
