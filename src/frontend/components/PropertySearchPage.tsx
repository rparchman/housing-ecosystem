import { useState } from 'react';
import { searchProperties } from '../api/propertySearchApi';
import { PropertySearchFilters } from './PropertySearchFilters';
import { PropertySearchResults } from './PropertySearchResults';
import { Pagination } from './Pagination';
import { PropertySearchQuery, PropertySearchResult } from '../models/propertySearch';

export function PropertySearchPage() {
  const [results, setResults] = useState<PropertySearchResult[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [lastQuery, setLastQuery] = useState<PropertySearchQuery>({});

  async function runSearch(query: PropertySearchQuery) {
    const data = await searchProperties(query);

    setResults(data.results);
    setTotalPages(data.totalPages);
    setPage(data.page);
    setLastQuery(query);
  }

  async function changePage(newPage: number) {
    const updatedQuery = { ...lastQuery, page: newPage };
    await runSearch(updatedQuery);
  }

  return (
    <div>
      <PropertySearchFilters onSearch={runSearch} />

      <PropertySearchResults results={results} />

      <Pagination
        page={page}
        totalPages={totalPages}
        onPageChange={changePage}
      />
    </div>
  );
}
