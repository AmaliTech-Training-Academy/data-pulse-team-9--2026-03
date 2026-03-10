"use client";

import FileUpload from "@/components/FileUpload";

export default function UploadPage() {
    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-primary">Upload Dataset</h2>
                <p className="text-gray-500">Add a new CSV or JSON file to validate.</p>
            </div>

            <FileUpload />
        </div>
    );
}
