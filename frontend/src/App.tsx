import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";
import { TopBar } from "@/components/TopBar";
import { queryClient } from "@/lib/queryClient";
import ComparePage from "@/pages/Compare";
import DataHealthPage from "@/pages/DataHealth";
import DesignPage from "@/pages/Design";
import FundDetailPage from "@/pages/FundDetail";
import FundsPage from "@/pages/Funds";
import OverviewPage from "@/pages/Overview";
import { PlaceholderPage } from "@/pages/Placeholder";

export default function App(): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex h-full w-full bg-surface text-fg">
          <Sidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <TopBar />
            <main className="flex-1 overflow-auto">
              <div className="mx-auto w-full max-w-page px-2 py-3">
                <Routes>
                  <Route path="/" element={<OverviewPage />} />
                  <Route path="/funds" element={<FundsPage />} />
                  <Route path="/funds/:code" element={<FundDetailPage />} />
                  <Route path="/compare" element={<ComparePage />} />
                  <Route path="/reports" element={<PlaceholderPage title="Reports" phase="Phase 7" />} />
                  <Route path="/data-health" element={<DataHealthPage />} />
                  <Route path="/design" element={<DesignPage />} />
                  <Route path="*" element={<PlaceholderPage title="Not found" phase="—" />} />
                </Routes>
              </div>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
