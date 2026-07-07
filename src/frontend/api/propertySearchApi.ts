import { PropertySearchQuery, PropertySearchResult } from '../models/propertySearch';
import { buildQueryString } from '../utils/buildQueryString';

const BASE_URL = 'http://localhost:3000'; // change for production

export async function searchProperties(
  query: PropertySearchQuery
): Promise<{
  results: PropertySearchResult[];
  total: number;
  totalPages: number;
  page: number;
  limit: number;
}> {
  const qs = buildQueryString(query);
  const url = `${BASE_URL}/properties/search${qs}`;

  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(`Search failed: ${res.status}`);
  }

  const results: PropertySearchResult[] = await res.json();

  const total = Number(res.headers.get('X-Total-Count') || 0);
  const totalPages = Number(res.headers.get('X-Total-Pages') || 1);
  const page = Number(res.headers.get('X-Page') || 1);
  const limit = Number(res.headers.get('X-Limit') || 25);

  return {
    results,
    total,
    totalPages,
    page,
    limit,
  };
}
