import { useCallback, useState } from "react";
import { ApiError, api } from "@/services/api/client";

export function useApi<T>() {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(false);

  const execute = useCallback(async (request: () => Promise<T>) => {
    setLoading(true);
    setError(null);
    try {
      const result = await request();
      setData(result);
      return result;
    } catch (caught) {
      const nextError = caught instanceof ApiError
        ? caught
        : new ApiError("Erreur réseau inattendue.", 0);
      setError(nextError);
      throw nextError;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, error, loading, execute, api };
}