import React, { useState } from 'react';
import { Paper, InputBase, IconButton, Box } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import SearchFilters from '../search/SearchFilters';

const SearchBar = ({ onSearch, initialQuery = '', showFilters = true }) => {
  const [query, setQuery] = useState(initialQuery);
  const [filters, setFilters] = useState({
    minYear: 0,
    minCitations: 0,
    topK: 60
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query, filters);
    }
  };

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Paper
        component="form"
        onSubmit={handleSubmit}
        sx={{
          p: '2px 4px',
          display: 'flex',
          alignItems: 'center',
          width: 400,
          bgcolor: 'background.paper',
          boxShadow: 3
        }}
      >
        <InputBase
          sx={{ ml: 1, flex: 1 }}
          placeholder="搜索论文..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <IconButton type="submit" sx={{ p: '10px' }}>
          <SearchIcon />
        </IconButton>
      </Paper>
      
      {showFilters && (
        <SearchFilters 
          filters={filters}
          onFilterChange={handleFilterChange}
        />
      )}
    </Box>
  );
};

export default SearchBar; 