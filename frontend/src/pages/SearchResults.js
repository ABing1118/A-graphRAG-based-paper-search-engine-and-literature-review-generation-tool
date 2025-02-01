import React, { useState, useRef } from 'react';
import { Box, Typography, Tabs, Tab } from '@mui/material';
import ParticleBackground from '../components/common/ParticleBackground';
import PaperList from '../components/papers/PaperList';
import PaperDetail from '../components/papers/PaperDetail';
import Navbar from '../components/common/Navbar';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import CitationNetwork from '../components/research/CitationNetwork';

const SearchResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState(location.state?.query || '');
  const [searchResults, setSearchResults] = useState(location.state?.results || []);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [_filters, setFilters] = useState({
    minYear: 0,
    minCitations: 0,
    topK: 60
  });
  const [activeTab, setActiveTab] = useState('network');
  const [selectedPaperId, setSelectedPaperId] = useState(null);
  const [hoveredPaperId, setHoveredPaperId] = useState(null);
  const paperListRef = useRef(null);

  const handleSearch = async (query, searchFilters) => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/search_papers', {
        params: { 
          query,
          min_year: searchFilters.minYear || undefined,
          min_citations: searchFilters.minCitations || undefined,
          top_k: searchFilters.topK
        }
      });
      setSearchResults(response.data.results);
      setSearchQuery(query);
      setFilters(searchFilters);
      
      navigate('/results', { 
        state: { 
          results: response.data.results,
          query: query,
          filters: searchFilters
        },
        replace: true 
      });
    } catch (err) {
      console.error('搜索失败:', err);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handlePaperSelect = (paper) => {
    setSelectedPaper(paper);
    setSelectedPaperId(paper.id);
  };

  const handleNodeClick = (node) => {
    console.log('Node data:', node);
    setSelectedPaperId(node.id);
    
    const selectedPaper = searchResults.find(p => p.id === node.id);
    console.log('Found paper:', selectedPaper);
    console.log('All papers:', searchResults);
    
    if (selectedPaper) {
        setSelectedPaper(selectedPaper);
        
        const paperElement = document.querySelector(`[data-paper-id="${node.id}"]`);
        if (paperElement) {
            paperElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    } else {
        console.warn('Paper not found in search results:', node.id);
    }
  };

  const handleNodeHover = (node) => {
    setHoveredPaperId(node ? node.id : null);
  };

  return (
    <Box sx={{ 
      minHeight: '100vh',
      bgcolor: 'background.default',
      color: 'text.primary',
      position: 'relative',
    }}>
      <ParticleBackground />
      
      <Box sx={{ position: 'relative', zIndex: 1 }}>
        <Navbar onSearch={handleSearch} showBackButton initialQuery={searchQuery} />
        
        <Box sx={{ display: 'flex', height: 'calc(100vh - 64px)' }}>
          {/* 左侧论文列表区域 */}
          <Box sx={{ 
            width: '25%', 
            borderRight: '1px solid rgba(255, 255, 255, 0.12)',
            height: '100%',
            overflow: 'auto',
            background: 'rgba(255, 255, 255, 0.2)',
            backdropFilter: 'blur(3px)'
          }}>
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom sx={{ color: 'primary.main' }}>
                "{searchQuery}" 相关论文
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                显示 {searchResults.length} 篇论文
                {location.state?.total > searchResults.length && 
                  `（共找到 ${location.state.total} 篇）`}
              </Typography>
            </Box>
            
            <PaperList 
              papers={searchResults} 
              selectedPaperId={selectedPaperId}
              hoveredPaperId={hoveredPaperId}
              onPaperSelect={handlePaperSelect}
              onPaperHover={setHoveredPaperId}
              ref={paperListRef}
            />
          </Box>

          {/* 中间引文网络区域 */}
          <Box sx={{ width: '50%', p: 2 }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs 
                value={activeTab} 
                onChange={handleTabChange}
                textColor="primary"
                indicatorColor="primary"
              >
                <Tab label="Citation Network" value="network" />
                <Tab label="Literature Review" value="review" />
              </Tabs>
            </Box>
            <Box sx={{ mt: 2, height: 'calc(100% - 48px)' }}>  {/* 48px 是 tabs 的高度 */}
              {activeTab === 'network' && (
                <CitationNetwork 
                  query={searchQuery} 
                  topK={_filters.topK}
                  onNodeClick={handleNodeClick}
                  onNodeHover={handleNodeHover}
                  selectedPaperId={selectedPaperId}
                  hoveredPaperId={hoveredPaperId}
                />
              )}
              {activeTab === 'review' && (
                <Box sx={{ p: 2 }}>
                  <Typography>Literature Review Component (Coming Soon)</Typography>
                </Box>
              )}
            </Box>
          </Box>

          {/* 右侧论文详情区域 */}
          <Box sx={{ width: '25%', p: 2, height: '100%', overflow: 'auto' }}>
            <PaperDetail paper={selectedPaper} />
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default SearchResults; 