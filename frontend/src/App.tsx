import { Route, Routes } from "react-router-dom";
import DetailPage from "./pages/DetailPage";
import InputPage from "./pages/InputPage";

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>AI PR Review 助手</h1>
        <p>结构化影响分析与审阅辅助（定稿 v2.0）</p>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<InputPage />} />
          <Route path="/tasks/:taskId" element={<DetailPage />} />
        </Routes>
      </main>
    </div>
  );
}
