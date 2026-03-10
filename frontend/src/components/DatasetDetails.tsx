"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/services/api";
import {
    ArrowLeft,
    FileText,
    FileJson,
    Calendar,
    Database,
    Hash,
    Loader2,
    CheckCircle,
    AlertTriangle,
    XCircle,
    Play
} from "lucide-react";
import Link from "next/link";

interface DatasetDetailsProps {
    id: string;
    backUrl: string;
}

interface DatasetData {
    id: number;
    name: string;
    file_type: string;
    row_count: number | null;
    column_count: number | null;
    column_names: any;
    status: string;
    uploaded_at: string;
}

interface ReportData {
    score: number;
    total_rules: number;
    checked_at: string;
    results: any[];
}

const getColumnNames = (cols: any): string[] => {
    if (!cols) return [];
    if (Array.isArray(cols)) return cols;
    if (typeof cols === 'string') {
        try {
            // Backend might send a stringified JSON array
            const parsed = JSON.parse(cols.replace(/'/g, '"'));
            if (Array.isArray(parsed)) return parsed;
        } catch {
            return cols.split(',').map(s => s.trim()).filter(Boolean);
        }
    }
    return [];
};

export default function DatasetDetails({ id, backUrl }: DatasetDetailsProps) {
    const [dataset, setDataset] = useState<DatasetData | null>(null);
    const [report, setReport] = useState<ReportData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadDetails = async () => {
            try {
                const token = localStorage.getItem("token");
                const options = { headers: { Authorization: `Bearer ${token}` } };

                const datasetRes = await fetchApi(`/datasets/${id}`, options);
                setDataset(datasetRes);

                try {
                    const reportRes = await fetchApi(`/reports/${id}`, options);
                    setReport(reportRes);
                } catch {
                    // Report might not exist yet if pending
                    setReport(null);
                }
            } catch (err: any) {
                setError(err.message || "Failed to load dataset details");
            } finally {
                setIsLoading(false);
            }
        };

        loadDetails();
    }, [id]);

    const getScoreColor = (score: number) => {
        if (score >= 80) return "text-success bg-success/10 border-success/20";
        if (score >= 50) return "text-warning bg-warning/10 border-warning/20";
        return "text-danger bg-danger/10 border-danger/20";
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px]">
                <Loader2 className="animate-spin text-accent mb-4" size={40} />
                <p className="text-gray-500 font-medium">Loading dataset details...</p>
            </div>
        );
    }

    if (error || !dataset) {
        return (
            <div className="bg-red-50 border border-red-200 text-red-600 p-6 rounded-xl flex flex-col items-center justify-center min-h-[300px]">
                <XCircle size={48} className="mb-4 text-red-500" />
                <h3 className="text-xl font-bold mb-2">Error Loading Dataset</h3>
                <p>{error || "Dataset not found"}</p>
                <Link href={backUrl} className="mt-6 px-4 py-2 bg-white text-gray-700 rounded-lg shadow-sm border border-gray-200 hover:bg-gray-50 transition-colors">
                    Go Back
                </Link>
            </div>
        );
    }

    const isCSV = dataset.file_type?.toUpperCase() === "CSV";
    const columnNames = getColumnNames(dataset.column_names);

    return (
        <div className="space-y-6">
            {/* Header / Nav */}
            <div className="flex items-center gap-4">
                <Link href={backUrl} className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-500 hover:text-primary transition-colors">
                    <ArrowLeft size={20} />
                </Link>
                <div>
                    <h2 className="text-2xl font-bold text-primary flex items-center gap-2">
                        {dataset.name}
                        {report ? (
                            <span className={`text-sm px-3 py-1 rounded-full border ${getScoreColor(report.score)} ml-3 font-semibold`}>
                                Quality Score: {report.score}%
                            </span>
                        ) : (
                            <span className="text-sm px-3 py-1 rounded-full border border-gray-200 bg-gray-50 text-gray-500 ml-3 font-semibold">
                                {dataset.status === "COMPLETED" ? "No Report Yet" : "Processing"}
                            </span>
                        )}
                    </h2>
                    <p className="text-gray-500 mt-1 flex items-center gap-2 text-sm">
                        Uploaded on {new Date(dataset.uploaded_at).toLocaleString()}
                        <span className="w-1 h-1 rounded-full bg-gray-300"></span>
                        Dataset ID: #{dataset.id}
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Main Info Card */}
                <div className="md:col-span-2 space-y-6">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <h3 className="text-lg font-bold text-primary mb-4 border-b border-gray-100 pb-2">Dataset Characteristics</h3>
                        <div className="grid grid-cols-2 gap-6">
                            <div className="flex items-start gap-3">
                                <div className={`p-2 rounded-lg mt-1 ${isCSV ? 'bg-blue-50 text-blue-600' : 'bg-yellow-50 text-yellow-600'}`}>
                                    {isCSV ? <FileText size={20} /> : <FileJson size={20} />}
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500 font-medium">Format</p>
                                    <p className="font-semibold text-primary">{dataset.file_type?.toUpperCase() || "CSV"}</p>
                                </div>
                            </div>

                            <div className="flex items-start gap-3">
                                <div className="p-2 bg-purple-50 text-purple-600 rounded-lg mt-1">
                                    <Database size={20} />
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500 font-medium">Total Rows</p>
                                    <p className="font-semibold text-primary">{dataset.row_count?.toLocaleString() || "Analyzing..."}</p>
                                </div>
                            </div>

                            <div className="flex items-start gap-3">
                                <div className="p-2 bg-green-50 text-green-600 rounded-lg mt-1">
                                    <Hash size={20} />
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500 font-medium">Total Columns</p>
                                    <p className="font-semibold text-primary">{dataset.column_count?.toLocaleString() || "Analyzing..."}</p>
                                </div>
                            </div>
                        </div>

                        {columnNames.length > 0 && (
                            <div className="mt-8">
                                <p className="text-sm text-gray-500 font-medium mb-3">Detected Columns</p>
                                <div className="flex flex-wrap gap-2">
                                    {columnNames.map((col, idx) => (
                                        <span key={idx} className="px-3 py-1 bg-gray-50 border border-gray-200 text-gray-700 text-xs font-semibold rounded-md">
                                            {col}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Sidebar Action / Status Map */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 text-center">
                        <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4
                            ${dataset.status === 'COMPLETED' ? 'bg-green-50 text-green-600' :
                                dataset.status === 'FAILED' ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600 animate-pulse'}`}>
                            {dataset.status === 'COMPLETED' ? <CheckCircle size={32} /> :
                                dataset.status === 'FAILED' ? <AlertTriangle size={32} /> : <Loader2 size={32} className="animate-spin" />}
                        </div>
                        <h3 className="font-bold text-lg text-primary mb-1">Status: {dataset.status}</h3>
                        <p className="text-sm text-gray-500 mb-6">Current processing status of this dataset on the platform.</p>

                        {!report && dataset.status === 'COMPLETED' && (
                            <button className="w-full flex items-center justify-center gap-2 bg-accent hover:bg-accent/90 text-white py-2.5 rounded-lg transition-colors font-medium">
                                <Play size={16} />
                                Run Quality Check
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
