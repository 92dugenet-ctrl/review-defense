// Hook transversal pour les appels API déclenchés par les composants React.
// Il conserve le résultat, l'état de chargement et l'erreur normalisée, puis expose execute()
// pour encapsuler une promesse métier. Les pages gardent la responsabilité du choix de l'endpoint
// et de la présentation ; le transport HTTP commun reste centralisé dans services/api/client.ts.

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