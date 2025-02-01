import React, { useState, useEffect } from 'react';
import { 
  Paper, 
  InputBase, 
  IconButton, 
  Box,
  Popper,
  List,
  ListItemButton,
  ListItemText,
  ClickAwayListener,
  Grow
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import SearchFilters from '../search/SearchFilters';

const SearchBar = ({ onSearch, initialQuery = '', showFilters = true }) => {
  const [query, setQuery] = useState(initialQuery);
  const [open, setOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [searchHistory, setSearchHistory] = useState([]);
  const [filters, setFilters] = useState({
    minYear: 0,
    minCitations: 0,
    topK: 60
  });

  // 加载搜索历史
  useEffect(() => {
    const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
    setSearchHistory(history);
  }, []);

  const addToHistory = (searchQuery) => {
    const newHistory = [searchQuery, ...searchHistory.filter(item => item !== searchQuery)].slice(0, 5);
    localStorage.setItem('searchHistory', JSON.stringify(newHistory));
    setSearchHistory(newHistory);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      addToHistory(query.trim());
      onSearch(query, filters);
      setOpen(false);
    }
  };

  const handleInputFocus = (event) => {
    // 防止事件冒泡
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    setOpen(true);
  };

  const handleClose = (event) => {
    // 防止事件冒泡
    if (event) {
      event.stopPropagation();
    }
    setOpen(false);
  };

  const handleSuggestionClick = (event, suggestion) => {
    // 防止事件冒泡
    event.stopPropagation();
    setQuery(suggestion);
    addToHistory(suggestion);
    onSearch(suggestion, filters);
    setOpen(false);
  };

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
  };

  const showPopper = open && Boolean(anchorEl) && searchHistory.length > 0;

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Paper
        component="form"
        onSubmit={handleSubmit}
        onClick={(e) => e.stopPropagation()}  // 防止点击表单时关闭
        sx={{
          p: '2px 4px',
          display: 'flex',
          alignItems: 'center',
          width: 400,
          bgcolor: 'background.paper',
          boxShadow: 3,
          position: 'relative'
        }}
      >
        <InputBase
          sx={{ ml: 1, flex: 1 }}
          placeholder="搜索论文..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={handleInputFocus}
          onClick={(e) => e.stopPropagation()}  // 防止点击输入框时关闭
        />
        <IconButton 
          type="submit" 
          sx={{ p: '10px' }}
          onClick={(e) => e.stopPropagation()}  // 防止点击按钮时关闭
        >
          <SearchIcon />
        </IconButton>
      </Paper>

      <Popper 
        open={showPopper}
        anchorEl={anchorEl}
        placement="bottom-start"
        transition
        style={{ zIndex: 1301 }}
        modifiers={[
          {
            name: 'offset',
            options: {
              offset: [0, 8],
            },
          },
        ]}
      >
        {({ TransitionProps }) => (
          <Grow {...TransitionProps}>
            <Paper 
              sx={{ 
                width: anchorEl?.offsetWidth || 400,
                maxHeight: 300, 
                overflow: 'auto',
                mt: -1,
                borderTopLeftRadius: 0,
                borderTopRightRadius: 0,
                boxShadow: 3,
                border: '1px solid #e0e0e0',
                borderTop: 'none'
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <ClickAwayListener onClickAway={handleClose}>
                <List>
                  {searchHistory.map((item, index) => (
                    <ListItemButton 
                      key={index} 
                      onClick={(e) => handleSuggestionClick(e, item)}
                      sx={{
                        '&:hover': {
                          bgcolor: 'action.hover'
                        },
                        py: 1
                      }}
                    >
                      <ListItemText 
                        primary={item}
                        primaryTypographyProps={{
                          fontSize: '0.9rem'
                        }}
                      />
                    </ListItemButton>
                  ))}
                </List>
              </ClickAwayListener>
            </Paper>
          </Grow>
        )}
      </Popper>
      
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