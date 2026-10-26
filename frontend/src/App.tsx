import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";
import { TopBar } from "@/components/TopBar";
import DesignPage from "@/pages/Design";
import { PlaceholderPage } from "@/pages/Placeholder";

export default function App(): JSX.Element {
  return (
    <BrowserRouter>
      <div className="flex h-full w-full bg-surface text-fg">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopBar />
          <main className="flex-1 overflow-auto">
            <div className="mx-auto w-full max-w-page px-2 py-3">
              <Routes>
                <Route path="/" element={<PlaceholderPage title="Overview" phase="Phase 6" />} />
                <Route path="/funds" element={<PlaceholderPage title="Funds" phase="Phase 6" />} />
                <Route path="/compare" element={<PlaceholderPage title="Compare" phase="Phase 6" />} />
                <Route path="/reports" element={<PlaceholderPage title="Reports" phase="Phase 7" />} />
                <Route path="/data-health" element={<PlaceholderPage title="Data Health" phase="Phase 6" />} />
                <Route path="/design" element={<DesignPage />} />
                <Route path="*" element={<PlaceholderPage title="Not found" phase="—" />} />
              </Routes>
            </div>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
