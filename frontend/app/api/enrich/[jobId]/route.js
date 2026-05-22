import { backendFetch } from "../../_backend";

export async function GET(_request, { params }) {
  const { jobId } = await params;

  return backendFetch(`/api/enrich/${jobId}`);
}
