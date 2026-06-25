import { useState, useEffect, useCallback } from 'react';
import { getLeads } from '../api/client';

export function useLeads(params = {}) {
  const [leads, setLeads] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      const res = await getLeads(params);
      setLeads(res.data.items || []);
      setTotal(res.data.total || 0);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(params)]);

  useEffect(() => {
    fetch();
    const interval = setInterval(fetch, 10000);
    return () => clearInterval(interval);
  }, [fetch]);

  return { leads, total, loading, error, refetch: fetch };
}
