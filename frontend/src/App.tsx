import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";

import { fetchDetailPageMeta } from "./api/client";
import { pageTransitionMotion } from "./components/motion/PageTransition";
import { readMotionTokens } from "./components/motion/readMotionTokens";
import DetailPage from "./pages/DetailPage";
import InputPage from "./pages/InputPage";

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
  const location = useLocation();
  const reduce = useReducedMotion();
  const tokens = readMotionTokens();
  const motionProps = pageTransitionMotion(!!reduce, tokens);

  const routes = (
    <Routes location={location}>
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

  return (
    <AnimatePresence mode="wait">
      {motionProps ? (
        <motion.div key={location.pathname} className="page-transition" {...motionProps}>
          {routes}
        </motion.div>
      ) : (
        <div key={location.pathname} className="page-transition">
          {routes}
        </div>
      )}
    </AnimatePresence>
  );
}
