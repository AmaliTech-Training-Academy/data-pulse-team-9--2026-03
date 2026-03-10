"use client";

import { useState, useRef } from "react";
import {
  UploadCloud,
  FileText,
  FileJson,
  X,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

export default function FileUpload() {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<
    "idle" | "uploading" | "success" | "error"
  >("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [progress, setProgress] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    const validTypes = ["text/csv", "application/json", "text/plain"];
    const extension = selectedFile.name.split(".").pop()?.toLowerCase();

    if (
      validTypes.includes(selectedFile.type) ||
      extension === "csv" ||
      extension === "json"
    ) {
      setFile(selectedFile);
      setUploadState("idle");
      setProgress(0);
    } else {
      setUploadState("error");
    }
  };

  const clearFile = () => {
    setFile(null);
    setUploadState("idle");
    setErrorMessage("");
    setProgress(0);
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploadState("uploading");
    setProgress(0);
    setErrorMessage("");

    // Simulate upload progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 10;
      });
    }, 100);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const API_URL =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

      const response = await fetch(`${API_URL}/datasets/upload`, {
        method: "POST",
        // Get token from localStorage if standard auth is used
        headers: {
          ...(localStorage.getItem("token")
            ? { Authorization: `Bearer ${localStorage.getItem("token")}` }
            : {}),
        },
        body: formData,
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.non_field_errors?.[0] ||
            response.statusText ||
            "An error occurred during upload"
        );
      }

      clearInterval(interval);
      setProgress(100);
      setUploadState("success");
    } catch (err: unknown) {
      clearInterval(interval);
      setUploadState("error");
      if (err instanceof Error) {
        setErrorMessage(err.message || "Failed to upload file.");
      } else {
        setErrorMessage("Failed to upload file.");
      }
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const isJSON = file?.name.toLowerCase().endsWith(".json");

  return (
    <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 w-full max-w-4xl mx-auto">
      {/* Upload Area */}
      {!file && uploadState !== "error" && (
        <div
          className={`relative flex flex-col items-center justify-center p-12 border-2 border-dashed rounded-xl transition-colors cursor-pointer ${
            dragActive
              ? "border-accent bg-accent/5"
              : "border-gray-300 bg-gray-50 hover:bg-gray-100 hover:border-gray-400"
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.json,application/json,text/csv"
            onChange={handleChange}
            className="hidden"
          />

          <div
            className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 ${dragActive ? "bg-accent/10 text-accent" : "bg-white text-gray-400 border border-gray-200 shadow-sm"}`}
          >
            <UploadCloud size={32} />
          </div>

          <h3 className="text-lg font-bold text-primary mb-1">
            Click to upload or drag and drop
          </h3>
          <p className="text-sm text-gray-500 mb-6 flex items-center gap-2">
            <FileText size={16} /> CSV or <FileJson size={16} /> JSON (max.
            50MB)
          </p>

          <button className="px-6 py-2 bg-primary text-white font-medium rounded-lg hover:bg-primary/90 transition-colors">
            Browse Files
          </button>
        </div>
      )}

      {/* Invalid File Type Error */}
      {uploadState === "error" && !file && (
        <div className="flex flex-col items-center justify-center p-12 border-2 border-danger/30 bg-danger/5 rounded-xl text-center">
          <AlertCircle size={48} className="text-danger mb-4" />
          <h3 className="text-lg font-bold text-danger mb-2">Upload Failed</h3>
          <p className="text-danger/70 mb-6">
            {errorMessage || "Please upload a valid CSV or JSON file."}
          </p>
          <button
            onClick={() => setUploadState("idle")}
            className="px-6 py-2 bg-danger text-white font-medium rounded-lg hover:opacity-90 transition-colors"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Selected File Preview */}
      {file && (
        <div className="space-y-6">
          {/* File Card */}
          <div className="flex items-center justify-between p-4 border border-accent/20 bg-accent/5 rounded-xl">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center text-accent shadow-sm border border-accent/10">
                {isJSON ? <FileJson size={24} /> : <FileText size={24} />}
              </div>
              <div>
                <h4 className="font-semibold text-primary truncate max-w-[200px] sm:max-w-xs">
                  {file.name}
                </h4>
                <p className="text-sm text-gray-500">
                  {formatFileSize(file.size)}
                </p>
              </div>
            </div>

            {uploadState === "idle" && (
              <button
                onClick={clearFile}
                className="p-2 text-gray-400 hover:text-danger hover:bg-danger/10 rounded-full transition-colors"
                title="Remove file"
              >
                <X size={20} />
              </button>
            )}
            {uploadState === "success" && (
              <CheckCircle2 size={24} className="text-success m-2" />
            )}
          </div>

          {/* Progress Bar */}
          {uploadState === "uploading" && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm font-medium">
                <span className="text-primary">Uploading...</span>
                <span className="text-accent">{progress}%</span>
              </div>
              <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Success Message */}
          {uploadState === "success" && (
            <div className="p-4 bg-success/10 border border-success/20 rounded-lg flex items-start gap-3 text-success">
              <CheckCircle2 className="flex-shrink-0 mt-0.5" size={20} />
              <div>
                <h4 className="font-semibold">Upload Complete</h4>
                <p className="text-sm mt-1 opacity-90">
                  Your dataset has been securely uploaded and is ready for
                  validation rules.
                </p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            {uploadState === "idle" && (
              <>
                <button
                  onClick={clearFile}
                  className="px-6 py-2.5 border border-gray-200 text-gray-600 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  className="px-6 py-2.5 bg-accent text-white font-medium rounded-lg hover:opacity-90 shadow-lg shadow-accent/20 transition-all active:scale-95"
                >
                  Submit & Upload
                </button>
              </>
            )}

            {uploadState === "success" && (
              <>
                <button
                  onClick={clearFile}
                  className="px-6 py-2.5 border border-gray-200 text-gray-600 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Upload Another
                </button>
                <button className="px-6 py-2.5 bg-primary text-white font-medium rounded-lg hover:bg-primary/90 shadow-lg transition-all">
                  Go to Rules Definition
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
