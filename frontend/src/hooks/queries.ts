/**
 * All React Query hooks used by the pages, in one place so query keys stay
 * consistent across the app (and invalidation after ingest hits all of them).
 */
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { SortKey } from "@/types/api";

export const qk = {
  stats:        ["stats"] as const,
  funds: (p: Record<string, unknown>) => ["funds", p] as const,
  fund:  (code: number) => ["fund", code] as const,
  compare: (codes: number[]) => ["compare", codes.join(",")] as const,
  categories:   ["categories"] as const,
  ingestStatus: ["ingest-status"] as const,
};

export function useStats() {
  return useQuery({ queryKey: qk.stats, queryFn: api.stats });
}

export function useFunds(params: {
  category?: string;
  search?: string;
  sort?: SortKey;
  order?: "asc" | "desc";
  limit?: number;
} = {}) {
  return useQuery({
    queryKey: qk.funds(params),
    queryFn: () => api.funds(params),
  });
}

export function useFund(code: number | null) {
  return useQuery({
    queryKey: code === null ? ["fund", "none"] : qk.fund(code),
    queryFn: () => api.fund(code as number),
    enabled: code !== null,
  });
}

export function useCompare(codes: number[]) {
  return useQuery({
    queryKey: qk.compare(codes),
    queryFn: () => api.compare(codes),
    enabled: codes.length >= 2,
  });
}

export function useCategories() {
  return useQuery({ queryKey: qk.categories, queryFn: api.categories });
}

export function useIngestStatus() {
  return useQuery({
    queryKey: qk.ingestStatus,
    queryFn: api.ingestStatus,
    refetchInterval: 10_000,  // mild polling so Data Health stays live
  });
}
