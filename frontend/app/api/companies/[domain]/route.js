import { backendFetch } from "../../_backend";

export async function GET(_request, { params }) {
  const { domain } = await params;

  return backendFetch(`/api/companies/${domain}`);
}
