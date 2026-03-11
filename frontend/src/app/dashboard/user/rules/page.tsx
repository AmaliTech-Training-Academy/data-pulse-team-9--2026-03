"use client";

import { useState, useEffect, useCallback } from "react";
import {
    ClipboardCheck,
    Plus,
    Search,
    Filter,
    Settings2,
    Trash2,
    Edit3,
    Database,
    Activity,
    Save,
    AlertCircle,
    ChevronLeft,
    ChevronRight,
    X,
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

export default function RulesPage() {
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
                dataset_type: selectedDatasetType === "all" ? undefined : selectedDatasetType,
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
    }, [isAddModalOpen, isEditModalOpen, formData.rule_type, formData.parameters]);

    // Sync parsedParams back to formData.parameters
    const updateParam = (key: string, value: unknown) => {
        const newParams = { ...parsedParams, [key]: value };
        setParsedParams(newParams);
        setFormData(prev => ({ ...prev, parameters: JSON.stringify(newParams) }));
    };

    const handleAddRule = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await createRule(formData);
            setIsAddModalOpen(false);
            fetchData();
        } catch (err: unknown) {
            alert(err instanceof Error ? err.message : "Failed to create rule");
        }
    };

    const handleEditRule = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!currentRule) return;
        try {
            await updateRule(currentRule.id, formData);
            setIsEditModalOpen(false);
            fetchData();
        } catch (err: unknown) {
            alert(err instanceof Error ? err.message : "Failed to update rule");
        }
    };

    const handleDeleteRule = async () => {
        if (!currentRule) return;
        try {
            await deleteRule(currentRule.id);
            setIsDeleteModalOpen(false);
            fetchData();
        } catch (err: unknown) {
            alert(err instanceof Error ? err.message : "Failed to delete rule");
        }
    };

    const openEditModal = (rule: ValidationRule) => {
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
    };

    const openDeleteModal = (rule: ValidationRule) => {
        setCurrentRule(rule);
        setIsDeleteModalOpen(true);
    };

    // Client-side pagination logic
    const totalItems = rules.length;
    const totalPages = Math.ceil(totalItems / pageSize);
    const paginatedRules = rules.slice((currentPage - 1) * pageSize, currentPage * pageSize);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-primary">Validation Rules</h2>
                    <p className="text-gray-500">
                        Define and manage data quality rules for your datasets.
                    </p>
                </div>
            </div>

            {/* Filters Bar */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                {/* Search */}
                <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-accent transition-colors">
                        <Search size={16} />
                    </div>
                    <input
                        type="text"
                        placeholder="Search rules..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="block w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none text-sm"
                    />
                </div>

                {/* Type Filter */}
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm">
                    <Database size={14} className="text-gray-400" />
                    <select
                        value={selectedDatasetType}
                        onChange={(e) => setSelectedDatasetType(e.target.value)}
                        className="bg-transparent outline-none cursor-pointer text-gray-700 w-full"
                    >
                        <option value="all">All Dataset Types</option>
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
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm">
                    <Activity size={14} className="text-gray-400" />
                    <select
                        value={selectedRuleType}
                        onChange={(e) => setSelectedRuleType(e.target.value)}
                        className="bg-transparent outline-none cursor-pointer text-gray-700 w-full"
                    >
                        <option value="">All Rule Types</option>
                        <option value="NOT_NULL">Not Null Check</option>
                        <option value="DATA_TYPE">Type Validation</option>
                        <option value="RANGE">Numerical Range</option>
                        <option value="UNIQUE">Uniqueness</option>
                        <option value="REGEX">Pattern Match</option>
                    </select>
                </div>

                {/* Severity Filter */}
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm">
                    <Filter size={14} className="text-gray-400" />
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

            {/* Rules Manager Content */}
            <div className="space-y-4">
                {/* Table Title & Actions */}
                <div className="flex justify-between items-center px-2">
                    <h3 className="font-bold text-gray-700 flex items-center gap-2 uppercase tracking-wider text-xs">
                        <Activity size={14} className="text-accent" /> Active Rules List
                    </h3>
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
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg font-medium transition-all text-sm shadow-sm hover:opacity-90 active:scale-95"
                    >
                        <Plus size={16} strokeWidth={3} />
                        Create New Rule
                    </button>
                </div>

                {/* Rules Table */}
                {loading ? (
                    <div className="bg-white p-24 rounded-xl border border-gray-100 flex flex-col items-center justify-center">
                        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-accent mb-4"></div>
                        <p className="text-gray-500 font-medium">Loading rules...</p>
                    </div>
                ) : error ? (
                    <div className="bg-white p-12 rounded-xl border border-danger/20 text-center">
                        <AlertCircle size={48} className="text-danger mx-auto mb-4" />
                        <h4 className="text-danger font-bold">Fetch Error</h4>
                        <p className="text-gray-500 mt-1">{error}</p>
                        <button onClick={fetchData} className="mt-6 px-6 py-2 bg-danger text-white rounded-lg hover:opacity-90 transition-colors">Retry Connection</button>
                    </div>
                ) : (
                    <div className="space-y-4">
                        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse min-w-[700px]">
                                    <thead>
                                        <tr className="bg-gray-50/50 border-b border-gray-100">
                                            <th className="py-4 px-6 text-[10px] font-bold text-gray-400 uppercase tracking-widest">Rule Name</th>
                                            <th className="py-4 px-6 text-[10px] font-bold text-gray-400 uppercase tracking-widest">Column</th>
                                            <th className="py-4 px-6 text-[10px] font-bold text-gray-400 uppercase tracking-widest">Type / Parameters</th>
                                            <th className="py-4 px-6 text-[10px] font-bold text-gray-400 uppercase tracking-widest text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-50">
                                        {paginatedRules.length > 0 ? (
                                            paginatedRules.map((rule) => (
                                                <tr key={rule.id} className="hover:bg-gray-50/50 transition-colors group">
                                                    <td className="py-4 px-6">
                                                        <div className="flex items-center gap-3">
                                                            <div className={`p-2 rounded-lg ${rule.severity === 'HIGH' ? 'bg-danger/5 text-danger' : rule.severity === 'MEDIUM' ? 'bg-warning/5 text-warning' : 'bg-success/5 text-success'}`}>
                                                                <ClipboardCheck size={18} />
                                                            </div>
                                                            <div className="flex flex-col">
                                                                <span className="font-bold text-primary">{rule.name}</span>
                                                                <span className="text-[10px] text-gray-400 font-medium uppercase">{rule.dataset_type}</span>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="py-4 px-6">
                                                        <span className="font-mono text-sm bg-gray-100 text-primary px-2 py-0.5 rounded border border-gray-200">
                                                            {rule.field_name}
                                                        </span>
                                                    </td>
                                                    <td className="py-4 px-6">
                                                        <div className="flex flex-col gap-1">
                                                            <span className="text-xs font-bold text-gray-600 flex items-center gap-1">
                                                                <Activity size={10} className="text-accent" /> {rule.rule_type}
                                                            </span>
                                                            <span className="text-[11px] text-gray-400 italic max-w-[180px] truncate" title={rule.parameters || ""}>
                                                                {rule.parameters || "No params set"}
                                                            </span>
                                                        </div>
                                                    </td>
                                                    <td className="py-4 px-6 text-right">
                                                        <div className="flex items-center justify-end gap-2">
                                                            <button
                                                                onClick={() => openEditModal(rule)}
                                                                className="p-2 text-gray-400 hover:text-accent hover:bg-accent/5 rounded-lg transition-all"
                                                                title="Edit Rule"
                                                            >
                                                                <Edit3 size={16} />
                                                            </button>
                                                            <button
                                                                onClick={() => openDeleteModal(rule)}
                                                                className="p-2 text-gray-400 hover:text-danger hover:bg-danger/5 rounded-lg transition-all"
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
                                                <td colSpan={4} className="py-20 text-center text-gray-400 italic">No rules found matching your filters.</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Pagination Footer */}
                        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                            <p className="text-xs text-gray-500 font-medium tracking-tight">
                                Displaying <span className="text-primary font-bold">{paginatedRules.length}</span> of <span className="text-primary font-bold">{totalItems}</span> total rules
                            </p>
                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-1">
                                    <button
                                        disabled={currentPage === 1}
                                        onClick={() => setCurrentPage(prev => prev - 1)}
                                        className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 transition-colors text-gray-600"
                                    >
                                        <ChevronLeft size={16} />
                                    </button>
                                    <div className="px-3 py-1 font-bold text-xs text-accent bg-accent/5 rounded border border-accent/10">
                                        {currentPage} / {totalPages || 1}
                                    </div>
                                    <button
                                        disabled={currentPage >= totalPages}
                                        onClick={() => setCurrentPage(prev => prev + 1)}
                                        className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-30 transition-colors text-gray-600"
                                    >
                                        <ChevronRight size={16} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Add/Edit Modal Overlay */}
            {(isAddModalOpen || isEditModalOpen) && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] flex flex-col overflow-hidden animate-in slide-in-from-bottom-8 duration-300">
                        <div className="p-6 border-b border-gray-100 bg-primary/5 text-primary flex items-center justify-between">
                            <h3 className="font-bold flex items-center gap-2 text-sm uppercase tracking-wide">
                                <Settings2 size={18} className="text-accent" /> {isEditModalOpen ? "Modify Rule Configuration" : "New Quality Constraint"}
                            </h3>
                            <button
                                onClick={() => { setIsAddModalOpen(false); setIsEditModalOpen(false); }}
                                className="p-1 hover:bg-gray-200 rounded-full transition-colors text-gray-400"
                            >
                                <X size={20} />
                            </button>
                        </div>

                        <form onSubmit={isAddModalOpen ? handleAddRule : handleEditRule} className="p-6 space-y-4 overflow-y-auto flex-1">
                            <div>
                                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1.5">Rule Identity</label>
                                <input
                                    required
                                    type="text"
                                    placeholder="e.g. Unique Transaction ID"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none text-sm transition-all"
                                />
                            </div>
                            <div>
                                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1.5">File Format</label>
                                <input
                                    required
                                    type="text"
                                    placeholder="csv, json..."
                                    value={formData.dataset_type}
                                    onChange={(e) => setFormData({ ...formData, dataset_type: e.target.value })}
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1.5">Target Column</label>
                                <input
                                    required
                                    type="text"
                                    placeholder="column_name"
                                    value={formData.field_name}
                                    onChange={(e) => setFormData({ ...formData, field_name: e.target.value })}
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none text-sm"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1.5">Validation Logic</label>
                                    <select
                                        value={formData.rule_type}
                                        onChange={(e) => setFormData({ ...formData, rule_type: e.target.value })}
                                        className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none text-xs font-bold text-gray-700"
                                    >
                                        <option value="NOT_NULL">Not Null</option>
                                        <option value="DATA_TYPE">Type Match</option>
                                        <option value="RANGE">Boundaries</option>
                                        <option value="UNIQUE">Duplicates</option>
                                        <option value="REGEX">Pattern</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1.5">Impact Level</label>
                                    <select
                                        value={formData.severity}
                                        onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                                        className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none text-xs font-bold text-gray-700"
                                    >
                                        <option value="LOW">Minor</option>
                                        <option value="MEDIUM">Warning</option>
                                        <option value="HIGH">Critical</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1.5">Configuration Parameters</label>
                                <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl space-y-4">
                                    {formData.rule_type === "RANGE" && (
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-1">
                                                <label className="text-[10px] font-bold text-gray-400 uppercase">Minimum</label>
                                                <input
                                                    type="number"
                                                    placeholder="Min value"
                                                    className="w-full px-3 py-1.5 bg-white border border-gray-200 rounded-lg outline-none text-xs"
                                                    value={(parsedParams.min as string | number) ?? ""}
                                                    onChange={(e) => updateParam("min", e.target.value === "" ? null : Number(e.target.value))}
                                                />
                                            </div>
                                            <div className="space-y-1">
                                                <label className="text-[10px] font-bold text-gray-400 uppercase">Maximum</label>
                                                <input
                                                    type="number"
                                                    placeholder="Max value"
                                                    className="w-full px-3 py-1.5 bg-white border border-gray-200 rounded-lg outline-none text-xs"
                                                    value={(parsedParams.max as string | number) ?? ""}
                                                    onChange={(e) => updateParam("max", e.target.value === "" ? null : Number(e.target.value))}
                                                />
                                            </div>
                                        </div>
                                    )}

                                    {formData.rule_type === "DATA_TYPE" && (
                                        <div className="space-y-1">
                                            <label className="text-[10px] font-bold text-gray-400 uppercase">Required Type</label>
                                            <select
                                                className="w-full px-3 py-1.5 bg-white border border-gray-200 rounded-lg outline-none text-xs"
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
                                            <label className="text-[10px] font-bold text-gray-400 uppercase">Regex Pattern</label>
                                            <input
                                                type="text"
                                                placeholder="e.g. ^[A-Z0-9]+$"
                                                className="w-full px-3 py-1.5 bg-white border border-gray-200 rounded-lg outline-none text-xs font-mono"
                                                value={(parsedParams.pattern as string) || ""}
                                                onChange={(e) => updateParam("pattern", e.target.value)}
                                            />
                                        </div>
                                    )}

                                    {["NOT_NULL", "UNIQUE"].includes(formData.rule_type) && (
                                        <div className="flex items-center gap-2 text-[10px] text-gray-400 font-medium py-1">
                                            <AlertCircle size={12} />
                                            No extra parameters needed.
                                        </div>
                                    )}

                                    <div className="pt-2 border-t border-gray-100">
                                        <label className="text-[8px] font-bold text-gray-400 uppercase tracking-widest block mb-1">Raw JSON (Preview)</label>
                                        <code className="text-[10px] font-mono text-accent block bg-white border border-gray-100 p-1 rounded">
                                            {formData.parameters || "{}"}
                                        </code>
                                    </div>
                                </div>
                            </div>

                            <div className="pt-4 flex gap-3">
                                <button
                                    type="button"
                                    onClick={() => { setIsAddModalOpen(false); setIsEditModalOpen(false); }}
                                    className="flex-1 px-4 py-3 border border-gray-200 text-gray-500 font-bold rounded-xl hover:bg-gray-50 transition-all text-sm"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 px-4 py-3 bg-accent text-white font-bold rounded-xl hover:opacity-95 transition-all shadow-lg shadow-accent/20 text-sm flex items-center justify-center gap-2 active:scale-95"
                                >
                                    <Save size={18} /> {isEditModalOpen ? "Update Constraint" : "Apply to Pipeline"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {isDeleteModalOpen && currentRule && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in duration-300">
                        <div className="p-8 text-center">
                            <div className="w-16 h-16 bg-danger/10 text-danger rounded-full flex items-center justify-center mx-auto mb-4">
                                <Trash2 size={32} />
                            </div>
                            <h3 className="text-xl font-bold text-primary mb-2">Delete Validation Rule?</h3>
                            <p className="text-gray-500 mb-6">
                                You are about to remove <span className="font-semibold text-primary">&quot;{currentRule.name}&quot;</span>.
                                This action cannot be undone and will affect future data quality checks.
                            </p>
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setIsDeleteModalOpen(false)}
                                    className="flex-1 px-6 py-2.5 border border-gray-200 text-gray-600 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                    No, Keep it
                                </button>
                                <button
                                    onClick={handleDeleteRule}
                                    className="flex-1 px-6 py-2.5 bg-danger text-white font-medium rounded-lg hover:bg-danger/90 shadow-lg shadow-danger/20 transition-all active:scale-[0.98]"
                                >
                                    Yes, Delete Rule
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
