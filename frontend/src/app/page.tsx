import FileUpload from "@/components/FileUpload";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black p-4">
      <main className="w-full max-w-4xl flex flex-col items-center justify-center gap-10">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-white sm:text-5xl mb-4">
            DataPulse
          </h1>
          <p className="text-lg leading-8 text-zinc-600 dark:text-zinc-400 max-w-2xl">
            Upload your CSV or JSON datasets to instantly validate data quality and generate comprehensive reports.
          </p>
        </div>

        <FileUpload />
      </main>
    </div>
  );
}
