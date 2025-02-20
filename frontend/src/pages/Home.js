import React from 'react';
import { SearchBar } from '../components/papers/SearchBar';
import { PaperList } from '../components/papers/PaperList';
import { usePaperSearch } from '../hooks/usePaperSearch';

export const Home = () => {
  const { results, loading, error, search } = usePaperSearch();

  return (
    <div>
      <h1>Paper Search</h1>
      <SearchBar onSearch={search} />
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <PaperList papers={results} />
    </div>
  );
}; 