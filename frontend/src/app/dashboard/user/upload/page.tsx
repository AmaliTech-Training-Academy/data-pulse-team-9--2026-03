"use client";

import FileUpload from "@/components/FileUpload";

export default function UploadPage() {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-xl font-black text-[#08293c]">UPLOAD DATASET</h2>
        <p className="text-[12px] font-medium text-gray-400 mt-1">
          Add a new CSV or JSON file to validate.
        </p>
      </div>

      <FileUpload />
    </div>
  );
}
