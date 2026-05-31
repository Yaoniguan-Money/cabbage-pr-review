import type { ReactNode } from "react";
import { Route, Routes } from "react-router-dom";
import DetailPage from "./pages/DetailPage";
import InputPage from "./pages/InputPage";
import { useEffect, useState } from "react";
import { fetchDetailPageMeta } from "./api/client";

function InputShell({ children }: { children: ReactNode }) {
  const [appName, setAppName] = useState("");
  const [appTagline, setAppTagline] = useState("");

  useEffect(() => {
    fetchDetailPageMeta()
      .then((meta) => {
        setAppName(meta.ui_strings.app_name);
        setAppTagline(meta.ui_strings.app_tagline);
      })
      .catch(() => {});
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>{appName || "\u00A0"}</h1>
        <p>{appTagline || "\u00A0"}</p>
      </header>
      <main>{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <InputShell>
            <InputPage />
          </InputShell>
        }
      />
      <Route path="/tasks/:taskId" element={<DetailPage />} />
    </Routes>
  );
}
