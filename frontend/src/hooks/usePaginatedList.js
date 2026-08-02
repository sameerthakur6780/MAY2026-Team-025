import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/apiClient";

function buildQuery(params) {
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      usp.set(key, value);
    }
  });
  const qs = usp.toString();
  return qs ? `?${qs}` : "";
}

// Shared fetch/pagination/loading/error state for every admin list page --
// they all hit a GET endpoint returning {items, page, per_page, total, pages}.
export function usePaginatedList(basePath, filters = {}) {
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], page: 1, per_page: 20, total: 0, pages: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const filtersKey = JSON.stringify(filters);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get(`${basePath}${buildQuery({ ...filters, page })}`);
      setData(result);
    } catch (err) {
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [basePath, filtersKey, page]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  // Filters changing (not page changing) should snap back to page 1.
  useEffect(() => {
    setPage(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtersKey]);

  return { ...data, loading, error, page, setPage, refetch };
}
