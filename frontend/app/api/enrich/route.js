import { backendFetch } from "../_backend";

export async function POST(request) {
  const body = await request.json();

  return backendFetch("/api/enrich", {
    method: "POST",
    body: JSON.stringify(body)
  });
}
