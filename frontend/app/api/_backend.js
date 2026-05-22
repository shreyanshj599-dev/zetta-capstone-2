const backendHostPort = process.env.BACKEND_HOSTPORT;
const BACKEND_URL = (
  process.env.BACKEND_URL || (backendHostPort ? `http://${backendHostPort}` : "http://localhost:8000")
).replace(/\/+$/, "");

export async function backendFetch(path, init = {}) {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init.headers || {})
    },
    cache: "no-store"
  });

  const text = await response.text();
  let payload = {};

  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = { detail: text || "Unexpected backend response" };
  }

  return Response.json(payload, { status: response.status });
}
