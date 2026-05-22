import { backendFetch } from "../_backend";

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.toString();

  return backendFetch(`/api/companies${query ? `?${query}` : ""}`);
}
