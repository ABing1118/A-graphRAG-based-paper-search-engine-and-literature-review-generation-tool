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
    { value: 0, label: '不限' },
    { value: currentYear - 1, label: '近1年' },
    { value: currentYear - 3, label: '近3年' },
    { value: currentYear - 5, label: '近5年' },
    { value: currentYear - 10, label: '近10年' }
  ];

  const citationOptions = [
    { value: 0, label: '不限' },
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
      <Tooltip title="筛选条件">
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
            <InputLabel>发表时间</InputLabel>
            <Select
              value={filters.minYear || 0}
              label="发表时间"
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
            <InputLabel>最少引用</InputLabel>
            <Select
              value={filters.minCitations || 0}
              label="最少引用"
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
            <InputLabel>结果数量</InputLabel>
            <Select
              value={filters.topK || 60}
              label="结果数量"
              onChange={(e) => onFilterChange('topK', e.target.value)}
              MenuProps={menuProps}
            >
              <MenuItem value={20}>20篇</MenuItem>
              <MenuItem value={40}>40篇</MenuItem>
              <MenuItem value={60}>60篇</MenuItem>
              <MenuItem value={100}>100篇</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Popover>
    </Box>
  );
};

export default SearchFilters; 