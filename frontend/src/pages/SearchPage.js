import React from 'react';
import { Box, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ParticleBackground from '../components/common/ParticleBackground';
import SearchBar from '../components/common/SearchBar';
import axios from 'axios';

const SearchPage = () => {
  const navigate = useNavigate();

  const handleSearch = async (query, filters) => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/search_papers', {
        params: { 
          query,
          min_year: filters.minYear || undefined,
          min_citations: filters.minCitations || undefined,
          top_k: filters.topK
        }
      });
      
      navigate('/results', { 
        state: { 
          results: response.data.results,
          query: query,
          filters: filters
        }
      });
    } catch (err) {
      console.error('搜索失败:', err);
    }
  };

  return (
    <Box sx={{ 
      minHeight: '100vh',
      bgcolor: 'background.default',
      color: 'text.primary',
      position: 'relative',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <ParticleBackground />
      
      <Box sx={{ 
        position: 'relative',
        zIndex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 4,
        mb: 10  // 向上偏移一点，视觉上更协调
      }}>
        {/* Logo和标题 */}
        <Typography 
          variant="h2" 
          component="h1"
          sx={{ 
            color: 'primary.main',
            fontWeight: 'bold',
            mb: 2,
            textAlign: 'center',
            fontSize: { xs: '2.5rem', sm: '3.5rem', md: '4rem' }
          }}
        >
          Paper Insight
        </Typography>
        
        {/* 副标题 */}
        <Typography 
          variant="h6" 
          sx={{ 
            color: 'text.secondary',
            mb: 4,
            textAlign: 'center',
            maxWidth: 600,
            px: 2
          }}
        >
          文献综述生成器
        </Typography>

        {/* 搜索框和过滤器 */}
        <Box sx={{ 
          width: '100%',
          maxWidth: 800,
          px: 3
        }}>
          <SearchBar 
            onSearch={handleSearch}
            showFilters={true}
            initialQuery=""
          />
        </Box>
      </Box>
    </Box>
  );
};

export default SearchPage; 