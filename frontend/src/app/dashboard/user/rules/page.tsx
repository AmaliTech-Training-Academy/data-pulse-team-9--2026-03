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

export default function UserRulesPage() {
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
  const pageSize = 10;

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
          <h2 className="text-2xl font-bold text-primary">Validation Rules</h2>
          <p className="text-gray-500">
            View and manage validation rules for your datasets.
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
          New Rule
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
            <option value="all">All Files</option>
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
          <p className="text-gray-500 font-medium">Loading rules...</p>
        </div>
      ) : error ? (
        <div className="p-8 bg-danger/5 border border-danger/20 rounded-xl text-center">
          <AlertCircle size={48} className="text-danger mx-auto mb-4" />
          <h3 className="text-lg font-bold text-danger">
            Failed to Load Rules
          </h3>
          <p className="text-danger/70">{error}</p>
          <button
            onClick={fetchData}
            className="mt-4 px-4 py-2 bg-danger text-white rounded-lg hover:bg-danger/90 transition-colors"
          >
            Retry
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
                      Rule Information
                    </th>
                    <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">
                      Type &amp; Parameters
                    </th>
                    <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">
                      Format
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
                              Target field:{" "}
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
                              {rule.parameters || "No configuration"}
                            </p>
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-2 text-sm text-gray-700 uppercase font-medium text-center">
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
                            {rule.is_active ? "Active" : "Disabled"}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-right">
                          <div className="flex items-center justify-end gap-2 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => openEditModal(rule)}
                              className="p-2 text-gray-400 hover:text-primary bg-white rounded-lg border border-gray-200 shadow-sm transition-colors"
                              title="Edit Configuration"
                            >
                              <Settings size={16} />
                            </button>
                            <button
                              onClick={() => openDeleteModal(rule)}
                              className="p-2 text-danger/70 hover:text-danger bg-white rounded-lg border border-danger/20 shadow-sm transition-colors"
                              title="Delete"
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
                        No rules match your criteria.
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
              <span className="text-primary">{totalItems}</span> entries
            </p>
            <div className="flex items-center gap-1">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((prev) => prev - 1)}
                className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:hover:bg-transparent transition-colors text-gray-600"
              >
                <ChevronLeft size={18} />
              </button>
              <div className="px-4 py-1.5 bg-accent/10 border border-accent/20 rounded-lg text-accent font-bold text-sm text-center">
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
                {isAddModalOpen
                  ? "New Validation Rule"
                  : "Edit Rule Parameters"}
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
                    Rule Label
                  </label>
                  <input
                    required
                    type="text"
                    placeholder="Identification name"
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none font-medium text-center"
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
                    placeholder="csv, json"
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none text-center uppercase"
                    value={formData.dataset_type}
                    onChange={(e) =>
                      setFormData({ ...formData, dataset_type: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-gray-700">
                    Target Character/Field
                  </label>
                  <input
                    required
                    type="text"
                    placeholder="Column name"
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none text-center"
                    value={formData.field_name}
                    onChange={(e) =>
                      setFormData({ ...formData, field_name: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-gray-700">
                    Rule Pattern
                  </label>
                  <select
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none cursor-pointer font-medium text-center"
                    value={formData.rule_type}
                    onChange={(e) =>
                      setFormData({ ...formData, rule_type: e.target.value })
                    }
                  >
                    <option value="NOT_NULL">Required Value</option>
                    <option value="DATA_TYPE">Type Constraint</option>
                    <option value="RANGE">Numerical Range</option>
                    <option value="UNIQUE">Unique Value</option>
                    <option value="REGEX">Pattern Match</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-gray-700">
                    Condition
                  </label>
                  <select
                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none cursor-pointer font-medium text-center"
                    value={formData.severity}
                    onChange={(e) =>
                      setFormData({ ...formData, severity: e.target.value })
                    }
                  >
                    <option value="LOW">Low Risk</option>
                    <option value="MEDIUM">Standard Risk</option>
                    <option value="HIGH">Critical Risk</option>
                  </select>
                </div>
                <div className="space-y-1.5 col-span-2">
                  <label className="text-sm font-semibold text-gray-700">
                    Parameters Setup
                  </label>
                  <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl space-y-4">
                    {formData.rule_type === "RANGE" && (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-gray-400 uppercase text-center block">
                            Minimum
                          </label>
                          <input
                            type="number"
                            placeholder="0"
                            className="w-full px-3 py-1.5 bg-white border border-gray-200 rounded-lg outline-none text-sm text-center"
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
                          <label className="text-[10px] font-bold text-gray-400 uppercase text-center block">
                            Maximum
                          </label>
                          <input
                            type="number"
                            placeholder="100"
                            className="w-full px-3 py-1.5 bg-white border border-gray-200 rounded-lg outline-none text-sm text-center"
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
                        <label className="text-[10px] font-bold text-gray-400 uppercase text-center block">
                          Enforce Type
                        </label>
                        <select
                          className="w-full px-3 py-1.5 bg-white border border-gray-200 rounded-lg outline-none text-sm text-center"
                          value={(parsedParams.type as string) || ""}
                          onChange={(e) => updateParam("type", e.target.value)}
                        >
                          <option value="">Choose...</option>
                          <option value="string">Text</option>
                          <option value="integer">Integer</option>
                          <option value="float">Decimal</option>
                          <option value="boolean">Logic</option>
                          <option value="datetime">Timestamp</option>
                        </select>
                      </div>
                    )}

                    {formData.rule_type === "REGEX" && (
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-gray-400 uppercase text-center block">
                          Pattern Expression
                        </label>
                        <input
                          type="text"
                          placeholder="Regex string"
                          className="w-full px-3 py-1.5 bg-white border border-gray-200 rounded-lg outline-none text-sm font-mono text-center"
                          value={(parsedParams.pattern as string) || ""}
                          onChange={(e) =>
                            updateParam("pattern", e.target.value)
                          }
                        />
                      </div>
                    )}

                    {["NOT_NULL", "UNIQUE"].includes(formData.rule_type) && (
                      <div className="flex items-center justify-center gap-2 text-xs text-gray-400 font-medium py-2">
                        <AlertCircle size={14} />
                        Automatic validation. No extra parameters needed.
                      </div>
                    )}
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
                  {isAddModalOpen ? "Register Rule" : "Update Config"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {isDeleteModalOpen && currentRule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in slide-in-from-bottom-8 duration-300 border-t-4 border-danger">
            <div className="p-8 text-center text-center">
              <div className="w-16 h-16 bg-danger/10 text-danger rounded-full flex items-center justify-center mx-auto mb-4">
                <Trash2 size={32} />
              </div>
              <h3 className="text-xl font-bold text-primary mb-2 text-center">
                Delete this rule?
              </h3>
              <p className="text-gray-500 mb-6 text-center">
                Rule{" "}
                <span className="font-semibold text-primary">
                  &quot;{currentRule.name}&quot;
                </span>{" "}
                will be immediately deactivated.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setIsDeleteModalOpen(false)}
                  className="flex-1 px-6 py-2.5 border border-gray-200 text-gray-600 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={handleDeleteRule}
                  className="flex-1 px-6 py-2.5 bg-danger text-white font-medium rounded-lg hover:bg-danger/90 shadow-lg shadow-danger/20 transition-all active:scale-[0.98]"
                >
                  Delete Rule
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
