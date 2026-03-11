"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Filter,
  Search,
  Settings,
  Trash2,
  Activity,
  Database,
  Plus,
  X,
  AlertCircle,
  Save,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import {
  getRules,
  createRule,
  updateRule,
  deleteRule,
  ValidationRule,
  RuleCreateData,
  GetRulesParams,
} from "@/services/rules";
import { getDatasets, Dataset } from "@/services/datasets";

// Status color helper adapted for is_active
const getStatusColor = (isActive: boolean) => {
  return isActive
    ? "text-success bg-success/10 border-success/20"
    : "text-gray-500 bg-gray-100 border-gray-200";
};

export default function AdminRulesPage() {
  const [rules, setRules] = useState<ValidationRule[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtering & Searching State
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDatasetType, setSelectedDatasetType] = useState("all");
  const [selectedRuleType, setSelectedRuleType] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState("");

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Modal state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [currentRule, setCurrentRule] = useState<ValidationRule | null>(null);

  // Form state
  const [formData, setFormData] = useState<RuleCreateData>({
    name: "",
    dataset_type: "",
    field_name: "",
    rule_type: "NOT_NULL",
    parameters: "",
    severity: "MEDIUM",
  });

  // Dynamic Parameters UI state
  const [parsedParams, setParsedParams] = useState<Record<string, unknown>>({});

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: GetRulesParams = {
        dataset_type:
          selectedDatasetType === "all" ? undefined : selectedDatasetType,
        search: searchTerm || undefined,
        rule_type: selectedRuleType || undefined,
        severity: selectedSeverity || undefined,
      };

      const [rulesData, datasetsData] = await Promise.all([
        getRules(params),
        getDatasets(),
      ]);

      setRules(rulesData);
      setDatasets(datasetsData);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  }, [selectedDatasetType, searchTerm, selectedRuleType, selectedSeverity]);

  // Debounced search
  useEffect(() => {
    const handler = setTimeout(() => {
      fetchData();
    }, 500);
    return () => clearTimeout(handler);
  }, [fetchData]);

  // Parse parameters when modal opens or rule_type changes
  useEffect(() => {
    if (isAddModalOpen || isEditModalOpen) {
      try {
        const p = formData.parameters ? JSON.parse(formData.parameters) : {};
        setParsedParams(p);
      } catch {
        setParsedParams({}); // Fallback for invalid JSON
      }
    }
  }, [
    isAddModalOpen,
    isEditModalOpen,
    formData.rule_type,
    formData.parameters,
  ]);

  // Sync parsedParams back to formData.parameters
  const updateParam = useCallback(
    (key: string, value: unknown) => {
      const newParams = { ...parsedParams, [key]: value };
      setParsedParams(newParams);
      setFormData((prev) => ({
        ...prev,
        parameters: JSON.stringify(newParams),
      }));
    },
    [parsedParams]
  );

  const handleAddRule = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      try {
        await createRule(formData);
        setIsAddModalOpen(false);
        fetchData();
      } catch (err: unknown) {
        alert(err instanceof Error ? err.message : "Failed to create rule");
      }
    },
    [formData, fetchData]
  );

  const handleEditRule = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!currentRule) return;
      try {
        await updateRule(currentRule.id, formData);
        setIsEditModalOpen(false);
        fetchData();
      } catch (err: unknown) {
        alert(err instanceof Error ? err.message : "Failed to update rule");
      }
    },
    [currentRule, formData, fetchData]
  );

  const handleDeleteRule = useCallback(async () => {
    if (!currentRule) return;
    try {
      await deleteRule(currentRule.id);
      setIsDeleteModalOpen(false);
      fetchData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete rule");
    }
  }, [currentRule, fetchData]);

  const openEditModal = useCallback((rule: ValidationRule) => {
    setCurrentRule(rule);
    setFormData({
      name: rule.name,
      dataset_type: rule.dataset_type,
      field_name: rule.field_name,
      rule_type: rule.rule_type,
      parameters: rule.parameters,
      severity: rule.severity,
    });
    setIsEditModalOpen(true);
  }, []);

  const openDeleteModal = useCallback((rule: ValidationRule) => {
    setCurrentRule(rule);
    setIsDeleteModalOpen(true);
  }, []);

  // Client-side pagination logic
  const totalItems = rules.length;
  const totalPages = Math.ceil(totalItems / pageSize);
  const paginatedRules = rules.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-primary">
            Global Validation Rules
          </h2>
          <p className="text-gray-500">
            View and manage all active validation rules configured across the
            system.
          </p>
        </div>
        <button
          onClick={() => {
            setFormData({
              name: "",
              dataset_type: "",
              field_name: "",
              rule_type: "NOT_NULL",
              parameters: "",
              severity: "MEDIUM",
            });
            setIsAddModalOpen(true);
          }}
          className="flex items-center gap-2 px-4 py-2 bg-accent text-white rounded-lg hover:opacity-90 shadow-sm transition-all"
        >
          <Plus size={18} />
          Add Rule
        </button>
      </div>

      {/* Filters Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
        {/* Search */}
        <div className="relative group col-span-1 md:col-span-1">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-accent transition-colors">
            <Search size={16} />
          </div>
          <input
            type="text"
            placeholder="Search rules..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none transition-all text-sm"
          />
        </div>

        {/* Dataset Type Filter */}
        <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
          <Database size={14} />
          <select
            value={selectedDatasetType}
            onChange={(e) => setSelectedDatasetType(e.target.value)}
            className="bg-transparent outline-none cursor-pointer text-gray-700 w-full"
          >
            <option value="all">All Types</option>
            {Array.from(new Set(datasets.map((ds) => ds.file_type))).map(
              (type) => (
                <option key={type} value={type}>
                  {type.toUpperCase()} Files
                </option>
              )
            )}
          </select>
        </div>

        {/* Rule Type Filter */}
        <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
          <Activity size={14} />
          <select
            value={selectedRuleType}
            onChange={(e) => setSelectedRuleType(e.target.value)}
            className="bg-transparent outline-none cursor-pointer text-gray-700 w-full"
          >
            <option value="">All Rules</option>
            <option value="NOT_NULL">Not Null</option>
            <option value="DATA_TYPE">Data Type</option>
            <option value="RANGE">Range</option>
            <option value="UNIQUE">Unique</option>
            <option value="REGEX">Regex</option>
          </select>
        </div>

        {/* Severity Filter */}
        <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
          <Filter size={14} />
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="bg-transparent outline-none cursor-pointer text-gray-700 w-full"
          >
            <option value="">All Severities</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
          </select>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex flex-col items-center justify-center p-24 bg-white rounded-xl border border-gray-100">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mb-4"></div>
          <p className="text-gray-500 font-medium">Fetching rules...</p>
        </div>
      ) : error ? (
        <div className="p-8 bg-danger/5 border border-danger/20 rounded-xl text-center">
          <AlertCircle size={48} className="text-danger mx-auto mb-4" />
          <h3 className="text-lg font-bold text-danger">Error Loading Rules</h3>
          <p className="text-danger/70">{error}</p>
          <button
            onClick={fetchData}
            className="mt-4 px-4 py-2 bg-danger text-white rounded-lg hover:bg-danger/90 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse min-w-[1000px]">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">
                      Rule Details
                    </th>
                    <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">
                      Type &amp; Parameters
                    </th>
                    <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">
                      Dataset Type
                    </th>
                    <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">
                      Severity
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
                  {paginatedRules.length > 0 ? (
                    paginatedRules.map((rule) => (
                      <tr
                        key={rule.id}
                        className="hover:bg-gray-50/50 transition-colors group"
                      >
                        <td className="py-4 px-6">
                          <div>
                            <span className="font-semibold text-primary">
                              {rule.name}
                            </span>
                            <div className="text-sm text-gray-500 mt-1 flex items-center gap-1.5">
                              Target Column:{" "}
                              <span className="font-mono bg-gray-100 px-1 py-0.5 rounded text-primary">
                                {rule.field_name}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <div>
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-gray-100 text-gray-700 border border-gray-200">
                              <Activity size={12} className="text-gray-500" />{" "}
                              {rule.rule_type}
                            </span>
                            <p
                              className="text-xs text-gray-500 mt-1.5 italic max-w-[200px] truncate"
                              title={rule.parameters || ""}
                            >
                              {rule.parameters || "No params"}
                            </p>
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-2 text-sm text-gray-700 uppercase font-medium">
                            {rule.dataset_type}
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <span
                            className={`px-2 py-1 rounded-md text-xs font-bold ${
                              rule.severity === "HIGH"
                                ? "bg-danger/10 text-danger"
                                : rule.severity === "MEDIUM"
                                  ? "bg-warning/10 text-warning"
                                  : "bg-success/10 text-success"
                            }`}
                          >
                            {rule.severity}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <span
                            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${getStatusColor(rule.is_active)}`}
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                            {rule.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-right">
                          <div className="flex items-center justify-end gap-2 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => openEditModal(rule)}
                              className="p-2 text-gray-400 hover:text-primary bg-white rounded-lg border border-gray-200 shadow-sm transition-colors"
                              title="Edit Rule"
                            >
                              <Settings size={16} />
                            </button>
                            <button
                              onClick={() => openDeleteModal(rule)}
                              className="p-2 text-danger/70 hover:text-danger bg-white rounded-lg border border-danger/20 shadow-sm transition-colors"
                              title="Delete Rule"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan={6}
                        className="py-12 text-center text-gray-500 italic"
                      >
                        No validation rules found matching your filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination Footer */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
            <p className="text-sm text-gray-500 font-medium">
              Showing{" "}
              <span className="text-primary">{paginatedRules.length}</span> of{" "}
              <span className="text-primary">{totalItems}</span> rules
            </p>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 border border-gray-200 rounded-lg px-2 py-1">
                <span className="text-xs text-gray-500 font-medium whitespace-nowrap">
                  Size:
                </span>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  className="bg-transparent text-sm font-semibold outline-none cursor-pointer"
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>
              <div className="flex items-center gap-1">
                <button
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage((prev) => prev - 1)}
                  className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:hover:bg-transparent transition-colors text-gray-600"
                >
                  <ChevronLeft size={18} />
                </button>
                <div className="px-4 py-1.5 bg-accent/10 border border-accent/20 rounded-lg text-accent font-bold text-sm">
                  {currentPage} / {totalPages || 1}
                </div>
                <button
                  disabled={currentPage >= totalPages}
                  onClick={() => setCurrentPage((prev) => prev + 1)}
                  className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:hover:bg-transparent transition-colors text-gray-600"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add/Edit Modal */}
      {(isAddModalOpen || isEditModalOpen) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] flex flex-col overflow-hidden animate-in slide-in-from-bottom-8 duration-300">
            <div className="flex items-center justify-between p-6 border-b border-gray-100 bg-primary/5">
              <h3 className="text-xl font-bold text-primary flex items-center gap-2">
                {isAddModalOpen ? (
                  <Plus size={20} className="text-accent" />
                ) : (
                  <Settings size={20} className="text-accent" />
                )}
                {isAddModalOpen ? "Create Global Rule" : "Edit Configuration"}
              </h3>
              <button
                onClick={() => {
                  setIsAddModalOpen(false);
                  setIsEditModalOpen(false);
                }}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <form
              onSubmit={isAddModalOpen ? handleAddRule : handleEditRule}
              className="p-6 space-y-4 overflow-y-auto flex-1"
            >
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5 col-span-2">
                  <label className="text-sm font-semibold text-gray-700">
                    Rule Name
                  </label>
                  <input
                    required
                    type="text"
                    placeholder="Display name for this rule"
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none font-medium"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-gray-700">
                    Dataset Type
                  </label>
                  <input
                    required
                    type="text"
                    placeholder="csv, json, etc."
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none"
                    value={formData.dataset_type}
                    onChange={(e) =>
                      setFormData({ ...formData, dataset_type: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-gray-700">
                    Target Column
                  </label>
                  {/* availableColumns is not used, so removed the conditional rendering */}
                  <input
                    required
                    type="text"
                    placeholder="Enter column name"
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none"
                    value={formData.field_name}
                    onChange={(e) =>
                      setFormData({ ...formData, field_name: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-gray-700">
                    Rule Type
                  </label>
                  <select
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none cursor-pointer font-medium"
                    value={formData.rule_type}
                    onChange={(e) =>
                      setFormData({ ...formData, rule_type: e.target.value })
                    }
                  >
                    <option value="NOT_NULL">Not Null Check</option>
                    <option value="DATA_TYPE">Type Validation</option>
                    <option value="RANGE">Numerical Range</option>
                    <option value="UNIQUE">Uniqueness Check</option>
                    <option value="REGEX">Pattern Match (Regex)</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-gray-700">
                    Severity
                  </label>
                  <select
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none cursor-pointer font-medium"
                    value={formData.severity}
                    onChange={(e) =>
                      setFormData({ ...formData, severity: e.target.value })
                    }
                  >
                    <option value="LOW">Low Impact</option>
                    <option value="MEDIUM">Medium Warning</option>
                    <option value="HIGH">Critical Blocker</option>
                  </select>
                </div>
                <div className="space-y-1.5 col-span-2">
                  <label className="text-sm font-semibold text-gray-700">
                    Configuration Parameters
                  </label>
                  <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl space-y-4">
                    {formData.rule_type === "RANGE" && (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-gray-400 uppercase">
                            Minimum
                          </label>
                          <input
                            type="number"
                            placeholder="Min value"
                            className="w-full px-3 py-1.5 bg-white border border-gray-200 rounded-lg outline-none text-sm"
                            value={(parsedParams.min as string | number) ?? ""}
                            onChange={(e) =>
                              updateParam(
                                "min",
                                e.target.value === ""
                                  ? null
                                  : Number(e.target.value)
                              )
                            }
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-gray-400 uppercase">
                            Maximum
                          </label>
                          <input
                            type="number"
                            placeholder="Max value"
                            className="w-full px-3 py-1.5 bg-white border border-gray-200 rounded-lg outline-none text-sm"
                            value={(parsedParams.max as string | number) ?? ""}
                            onChange={(e) =>
                              updateParam(
                                "max",
                                e.target.value === ""
                                  ? null
                                  : Number(e.target.value)
                              )
                            }
                          />
                        </div>
                      </div>
                    )}

                    {formData.rule_type === "DATA_TYPE" && (
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-gray-400 uppercase">
                          Required Type
                        </label>
                        <select
                          className="w-full px-3 py-1.5 bg-white border border-gray-200 rounded-lg outline-none text-sm"
                          value={(parsedParams.type as string) || ""}
                          onChange={(e) => updateParam("type", e.target.value)}
                        >
                          <option value="">Select type...</option>
                          <option value="string">String</option>
                          <option value="integer">Integer</option>
                          <option value="float">Float</option>
                          <option value="boolean">Boolean</option>
                          <option value="datetime">DateTime</option>
                        </select>
                      </div>
                    )}

                    {formData.rule_type === "REGEX" && (
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-gray-400 uppercase">
                          Regex Pattern
                        </label>
                        <input
                          type="text"
                          placeholder="e.g. ^[A-Z0-9]+$"
                          className="w-full px-3 py-1.5 bg-white border border-gray-200 rounded-lg outline-none text-sm font-mono"
                          value={(parsedParams.pattern as string) || ""}
                          onChange={(e) =>
                            updateParam("pattern", e.target.value)
                          }
                        />
                      </div>
                    )}

                    {["NOT_NULL", "UNIQUE"].includes(formData.rule_type) && (
                      <div className="flex items-center gap-2 text-xs text-gray-400 font-medium py-2">
                        <AlertCircle size={14} />
                        No specific parameters required for this rule type.
                      </div>
                    )}

                    <div className="pt-2 border-t border-gray-200">
                      <label className="text-[9px] font-bold text-gray-400 uppercase tracking-widest block mb-1">
                        Raw JSON (Preview)
                      </label>
                      <code className="text-[10px] font-mono text-accent block bg-gray-100 p-1 rounded">
                        {formData.parameters || "{}"}
                      </code>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => {
                    setIsAddModalOpen(false);
                    setIsEditModalOpen(false);
                  }}
                  className="px-6 py-2 border border-gray-200 text-gray-600 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex items-center gap-2 px-6 py-2 bg-accent text-white font-medium rounded-lg hover:opacity-90 shadow-lg shadow-accent/20 transition-all active:scale-[0.98]"
                >
                  <Save size={18} />
                  {isAddModalOpen ? "Deploy Global Rule" : "Update Rule"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {isDeleteModalOpen && currentRule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in slide-in-from-bottom-8 duration-300">
            <div className="p-8 text-center">
              <div className="w-16 h-16 bg-danger/10 text-danger rounded-full flex items-center justify-center mx-auto mb-4">
                <Trash2 size={32} />
              </div>
              <h3 className="text-xl font-bold text-primary mb-2">
                Permanent Deletion?
              </h3>
              <p className="text-gray-500 mb-6">
                You are about to deactivate the rule{" "}
                <span className="font-semibold text-primary">
                  &quot;{currentRule.name}&quot;
                </span>
                . This will stop all quality checks associated with it.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setIsDeleteModalOpen(false)}
                  className="flex-1 px-6 py-2.5 border border-gray-200 text-gray-600 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteRule}
                  className="flex-1 px-6 py-2.5 bg-danger text-white font-medium rounded-lg hover:bg-danger/90 shadow-lg shadow-danger/20 transition-all active:scale-[0.98]"
                >
                  Deactivate Rule
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
