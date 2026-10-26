import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,            // 1 min — scorecards don't move intra-session
      gcTime:    10 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
