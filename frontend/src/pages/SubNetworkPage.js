import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import SubNetwork from '../components/research/SubNetwork';
import { fetchPaperSubNetwork } from '../api/papers';

const SubNetworkPage = () => {
    const [networkData, setNetworkData] = useState(null);
    const [loading, setLoading] = useState(true);
    const location = useLocation();
    const abortControllerRef = useRef(null);
    
    // 添加一个函数来判断数据是否准备就绪
    const isDataReady = (data) => {
        return data && data.nodes && data.edges && 
               data.nodes.length > 0 && 
               !loading;
    };
    
    useEffect(() => {
        const fetchData = async () => {
            try {
                const params = new URLSearchParams(location.search);
                const paperId = params.get('paperId');
                const paperTitle = decodeURIComponent(params.get('title') || '');
                
                if (!paperId) {
                    throw new Error('No paper ID provided');
                }
                
                setLoading(true);
                
                abortControllerRef.current = new AbortController();
                
                const data = await fetchPaperSubNetwork(paperId, abortControllerRef.current.signal);
                if (data && data.nodes && data.nodes.length > 0) {
                    data.nodes[0].title = paperTitle;
                }
                setNetworkData(data);
            } catch (error) {
                if (error.message === 'Request canceled') {
                    console.log('Request was canceled');
                } else {
                    console.error('Failed to fetch sub-network:', error);
                }
            } finally {
                setLoading(false);
            }
        };
        
        fetchData();

        return () => {
            if (abortControllerRef.current) {
                console.log('Aborting request due to page close...');
                abortControllerRef.current.abort();
                abortControllerRef.current = null;
            }
        };
    }, []);
    
    return (
        <Box sx={{ 
            width: '100vw', 
            height: '100vh', 
            bgcolor: 'background.paper',
            display: 'flex',
            flexDirection: 'column'
        }}>
            <Box sx={{ 
                p: 2, 
                borderBottom: 1, 
                borderColor: 'divider',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <Typography variant="h6">
                    {!isDataReady(networkData) ? 
                        "Loading..." : 
                        `Citation network of "${networkData.nodes[0].title}"`}
                </Typography>
            </Box>
            
            <Box sx={{ 
                flex: 1, 
                position: 'relative',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center'
            }}>
                {!isDataReady(networkData) ? (
                    // 显示加载状态
                    <Box sx={{ 
                        display: 'flex', 
                        flexDirection: 'column', 
                        alignItems: 'center',
                        gap: 2 
                    }}>
                        <CircularProgress />
                        <Typography>
                            Loading sub-network...
                        </Typography>
                    </Box>
                ) : (
                    // 显示网络图
                    <SubNetwork 
                        data={networkData}
                        loading={false}  // 数据准备就绪时，loading 一定是 false
                        fullPage={true}
                    />
                )}
            </Box>
        </Box>
    );
};

export default SubNetworkPage; 