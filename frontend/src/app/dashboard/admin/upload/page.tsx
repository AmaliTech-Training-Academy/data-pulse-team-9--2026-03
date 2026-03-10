"use client";

import FileUpload from "@/components/FileUpload";

export default function AdminUploadPage() {
    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-primary">Upload Dataset</h2>
                <p className="text-gray-500">Upload a new dataset directly to the system. This dataset will be available globally for validation.</p>
            </div>

            <FileUpload />
        </div>
    );
}
