import { lazy, StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const LandingPage = lazy(() => import("./LandingPage"));
const ReplayApp = lazy(() => import("./App"));

export function RouteShell() {
  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  const replay = path === "/replay";
  document.title = replay ? "Dhurandhar · Change Replay" : "Dhurandhar · Evidence before autonomy";

  return (
    <Suspense fallback={<main className="route-skeleton" aria-busy="true"><span className="brand-mark large">D</span><p>Loading verified evidence…</p></main>}>
      {replay ? <ReplayApp /> : <LandingPage />}
    </Suspense>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouteShell />
  </StrictMode>,
);
