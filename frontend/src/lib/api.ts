/**
 * Thin typed fetch wrapper around the Phase 4 API. The Vite dev server
 * proxies /api → http://localhost:8000, so the base URL stays empty.
 */
import type {
  CategorySummary,
  CompareResponse,
  FundDetail,
  FundSummary,
  IngestionStatus,
  SortKey,
  Stats,
} from "@/types/api";

const BASE = "";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function get<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Accept: "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new ApiError(detail || `HTTP ${res.status}`, res.status);
  }
  return (await res.json()) as T;
}

export const api = {
  stats: () => get<Stats>("/api/stats"),

  funds: (params: {
    category?: string;
    search?: string;
    sort?: SortKey;
    order?: "asc" | "desc";
    limit?: number;
  } = {}) => {
    const q = new URLSearchParams();
    if (params.category) q.set("category", params.category);
    if (params.search) q.set("search", params.search);
    if (params.sort) q.set("sort", params.sort);
    if (params.order) q.set("order", params.order);
    if (params.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return get<FundSummary[]>(`/api/funds${qs ? "?" + qs : ""}`);
  },

  fund: (code: number) => get<FundDetail>(`/api/funds/${code}`),

  compare: (codes: number[]) =>
    get<CompareResponse>(`/api/compare?codes=${codes.join(",")}`),

  categories: () => get<CategorySummary[]>("/api/categories/summary"),

  ingestStatus: () => get<IngestionStatus>("/api/ingest/status"),

  triggerIngest: async () => {
    const res = await fetch(`${BASE}/api/ingest`, { method: "POST" });
    if (!res.ok) throw new ApiError(`HTTP ${res.status}`, res.status);
    return res.json();
  },
};
