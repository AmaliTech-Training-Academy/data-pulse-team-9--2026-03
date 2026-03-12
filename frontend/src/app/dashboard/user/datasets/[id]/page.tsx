import DatasetDetails from "@/components/DatasetDetails";

export async function generateStaticParams() {
  return [];
}

export default async function UserDatasetDetailsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <DatasetDetails id={id} backUrl="/dashboard/user/datasets" />;
}
