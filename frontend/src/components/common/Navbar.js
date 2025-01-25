import React from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Box, 
  IconButton 
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import SearchBar from './SearchBar';

const Navbar = ({ onSearch, showBackButton = false, initialQuery = '' }) => {
  const navigate = useNavigate();

  const handleBack = () => {
    navigate('/');
  };

  return (
    <AppBar position="sticky" sx={{ bgcolor: 'background.paper', boxShadow: 1 }}>
      <Toolbar>
        {showBackButton && (
          <IconButton 
            edge="start" 
            onClick={handleBack}
            sx={{ mr: 2 }}
          >
            <ArrowBack />
          </IconButton>
        )}
        
        <Typography 
          variant="h6" 
          component="div" 
          sx={{ 
            flexGrow: 0,
            minWidth: 150,
            color: 'primary.main',
            fontWeight: 'bold',
            cursor: 'pointer'
          }}
          onClick={() => navigate('/')}
        >
          Paper Insight
        </Typography>

        <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center' }}>
          <SearchBar 
            onSearch={onSearch} 
            initialQuery={initialQuery}
            showFilters={true}  // 显示筛选器
          />
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar; 