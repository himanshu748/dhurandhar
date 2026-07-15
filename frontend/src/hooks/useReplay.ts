import { useCallback, useEffect, useState } from "react";
import { fetchReplay } from "../api";
import type { ReplaySnapshot } from "../types";

export const useReplay = () => {
  const [snapshot, setSnapshot] = useState<ReplaySnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const next = await fetchReplay();
      setSnapshot(next);
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load replay");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { snapshot, loading, error, refresh };
};
