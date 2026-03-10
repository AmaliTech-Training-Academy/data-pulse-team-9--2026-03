"use client";

import { useState, useEffect } from "react";
import {
    Search,
    Filter,
    FileText,
    FileJson,
    Play,
    Eye,
    Settings,
    Trash2,
    Loader2
} from "lucide-react";
import { fetchApi } from "@/services/api";
import Link from "next/link";

// Helper functions

const getStatusColor = (status: string) => {
    switch (status) {
        case "Clean": return "text-success";
        case "Good": return "text-success";
        case "Review Needed": return "text-warning";
        case "Critical Issues": return "text-danger";
        case "PROCESSING": return "text-gray-500 animate-pulse";
        default: return "text-gray-500";
    }
};

interface DatasetRow {
    id: number;
    name: string;
    type: string;
    date: string;
    status: string;
}

export default function MyDatasetsPage() {
    const [searchTerm, setSearchTerm] = useState("");
    const [datasets, setDatasets] = useState<DatasetRow[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            try {
                const token = localStorage.getItem("token");
                const options = {
                    headers: { Authorization: `Bearer ${token}` }
                };

                // Fetch only datasets, no scores
                const [datasetsData] = await Promise.all([
                    fetchApi("/datasets", options)
                ]);

                const datasetsArray = Array.isArray(datasetsData) ? datasetsData : (datasetsData?.results || datasetsData?.datasets || []);

                const processed = datasetsArray.map((d: { id: number; name?: string; file_type?: string; uploaded_at: string; status: string }) => {
                    return {
                        id: d.id,
                        name: d.name || `dataset_file_${d.id}.${d.file_type || 'csv'}`,
                        type: (d.file_type || 'CSV').toUpperCase(),
                        date: new Date(d.uploaded_at).toLocaleDateString(),
                        status: d.status
                    };
                });

                setDatasets(processed);
            } catch (err) {
                console.error("Failed to load datasets:", err);
            } finally {
                setIsLoading(false);
            }
        };

        loadData();
    }, []);

    const filteredDatasets = datasets.filter((d) =>
        d.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="space-y-6">

            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-primary">My Datasets</h2>
                <p className="text-gray-500">Manage and validate your uploaded data files.</p>
            </div>

            {/* Filters & Actions Bar */}
            <div className="flex flex-col sm:flex-row gap-4 justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-gray-100">

                {/* Search */}
                <div className="relative w-full sm:w-96 group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-accent transition-colors">
                        <Search size={18} />
                    </div>
                    <input
                        type="text"
                        placeholder="Search datasets..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="block w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none transition-all text-sm"
                    />
                </div>

                {/* Filters */}
                <div className="flex items-center gap-3 w-full sm:w-auto">
                    <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
                        <Filter size={16} />
                        <select className="bg-transparent outline-none cursor-pointer">
                            <option value="all">All Types</option>
                            <option value="csv">CSV</option>
                            <option value="json">JSON</option>
                        </select>
                    </div>

                    <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
                        <select className="bg-transparent outline-none cursor-pointer">
                            <option value="all">Any Score</option>
                            <option value="high">High (80-100)</option>
                            <option value="medium">Medium (50-79)</option>
                            <option value="low">Low (0-49)</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Datasets Table */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse min-w-[800px]">
                        <thead>
                            <tr className="bg-gray-50 border-b border-gray-200">
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">File Name</th>
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">Type</th>
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">Upload Date</th>
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider">Status</th>
                                <th className="py-4 px-6 text-xs font-bold text-primary uppercase tracking-wider text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {isLoading ? (
                                <tr>
                                    <td colSpan={7} className="py-12 text-center">
                                        <Loader2 className="animate-spin text-accent mx-auto mb-4" size={32} />
                                        <p className="text-gray-500 font-medium">Loading datasets...</p>
                                    </td>
                                </tr>
                            ) : filteredDatasets.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="py-12 text-center">
                                        <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                            <Search className="text-gray-400" size={24} />
                                        </div>
                                        <h3 className="text-lg font-bold text-primary mb-1">No datasets found</h3>
                                        <p className="text-gray-500">Try adjusting your filters or upload a new dataset.</p>
                                    </td>
                                </tr>
                            ) : (
                                filteredDatasets.map((dataset) => (
                                    <tr key={dataset.id} className="hover:bg-[#F4F6F8]/50 transition-colors group">
                                        <td className="py-4 px-6">
                                            <div className="flex items-center gap-3">
                                                <div className={`p-2 rounded-lg ${dataset.type === 'CSV' ? 'bg-blue-50 text-blue-600' : 'bg-yellow-50 text-yellow-600'}`}>
                                                    {dataset.type === 'CSV' ? <FileText size={18} /> : <FileJson size={18} />}
                                                </div>
                                                <span className="font-semibold text-primary">{dataset.name}</span>
                                            </div>
                                        </td>
                                        <td className="py-4 px-6">
                                            <span className="text-sm font-medium text-gray-600 border border-gray-200 bg-gray-50 px-2 py-1 rounded-md">
                                                {dataset.type}
                                            </span>
                                        </td>
                                        <td className="py-4 px-6 text-sm text-gray-500">{dataset.date}</td>
                                        <td className="py-4 px-6 text-sm font-medium">
                                            <span className={`flex items-center gap-1.5 ${getStatusColor(dataset.status)}`}>
                                                <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                                                {dataset.status}
                                            </span>
                                        </td>
                                        <td className="py-4 px-6 text-right">
                                            <div className="flex items-center justify-end gap-2 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity">
                                                <button className="p-2 text-gray-400 hover:text-accent bg-white rounded-lg border border-gray-200 shadow-sm transition-colors" title="Run Check">
                                                    <Play size={16} />
                                                </button>
                                                <Link href={`/dashboard/user/datasets/${dataset.id}`} className="p-2 text-gray-400 hover:text-primary bg-white rounded-lg border border-gray-200 shadow-sm transition-colors" title="View Details">
                                                    <Eye size={16} />
                                                </Link>
                                                <button className="p-2 text-gray-400 hover:text-primary bg-white rounded-lg border border-gray-200 shadow-sm transition-colors" title="Manage Rules">
                                                    <Settings size={16} />
                                                </button>
                                                <button className="p-2 text-gray-400 hover:text-danger bg-white rounded-lg border border-gray-200 shadow-sm transition-colors cursor-pointer" title="Delete Dataset">
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    );
}
