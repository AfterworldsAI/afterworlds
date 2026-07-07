import { useEffect, useState } from "react";

type HealthStatus = "checking" | "ok" | "error";

export default function App() {
  const [health, setHealth] = useState<HealthStatus>("checking");

  useEffect(() => {
    let cancelled = false;
    fetch("/api/health")
      .then((res) => (res.ok ? setHealth2("ok") : setHealth2("error")))
      .catch(() => setHealth2("error"));

    function setHealth2(status: HealthStatus): void {
      if (!cancelled) setHealth(status);
    }

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main>
      <h1>Afterworlds</h1>
      <p data-testid="health-status">API status: {health}</p>
    </main>
  );
}
