import React from 'react';
import { 
  Box, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem,
  IconButton,
  Tooltip,
  Popover,
  Paper
} from '@mui/material';
import { FilterList } from '@mui/icons-material';

const SearchFilters = ({ filters, onFilterChange }) => {
  const [anchorEl, setAnchorEl] = React.useState(null);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);

  const currentYear = new Date().getFullYear();
  const yearOptions = [
    { value: 0, label: 'No limit' },
    { value: currentYear - 1, label: 'Last year' },
    { value: currentYear - 3, label: 'Last 3 years' },
    { value: currentYear - 5, label: 'Last 5 years' },
    { value: currentYear - 10, label: 'Last 10 years' }
  ];

  const citationOptions = [
    { value: 0, label: 'No limit' },
    { value: 10, label: '10+' },
    { value: 50, label: '50+' },
    { value: 100, label: '100+' },
    { value: 500, label: '500+' }
  ];

  // 添加 MenuProps 配置
  const menuProps = {
    PaperProps: {
      sx: {
        bgcolor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        '& .MuiMenuItem-root': {
          '&:hover': {
            bgcolor: 'rgba(25, 118, 210, 0.08)', // 悬停效果
          },
        },
      },
    },
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Tooltip title="Filter conditions">
        <IconButton onClick={handleClick}>
          <FilterList />
        </IconButton>
      </Tooltip>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        PaperProps={{
          sx: {
            bgcolor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
          }
        }}
      >
        <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 200 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Publication time</InputLabel>
            <Select
              value={filters.minYear || 0}
              label="Publication time"
              onChange={(e) => onFilterChange('minYear', e.target.value)}
              MenuProps={menuProps}
            >
              {yearOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth size="small">
            <InputLabel>Minimum citations</InputLabel>
            <Select
              value={filters.minCitations || 0}
              label="Minimum citations"
              onChange={(e) => onFilterChange('minCitations', e.target.value)}
              MenuProps={menuProps}
            >
              {citationOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth size="small">
            <InputLabel>Result number</InputLabel>
            <Select
              value={filters.topK || 60}
              label="Result number"
              onChange={(e) => onFilterChange('topK', e.target.value)}
              MenuProps={menuProps}
            >
              <MenuItem value={20}>20 papers</MenuItem>
              <MenuItem value={40}>40 papers</MenuItem>
              <MenuItem value={60}>60 papers</MenuItem>
              <MenuItem value={100}>100 papers</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Popover>
    </Box>
  );
};

export default SearchFilters; 