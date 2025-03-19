import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';
import axios from 'axios';

const LiteratureReview = ({ query }) => {
    const [review, setReview] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentQuery, setCurrentQuery] = useState(null);
    const [lastReviewTimestamp, setLastReviewTimestamp] = useState(null);

    useEffect(() => {
        // 当 query 改变时，重置状态
        if (query !== currentQuery) {
            setLoading(true);
            setReview(null);
            setError(null);
            setCurrentQuery(query);
            setLastReviewTimestamp(Date.now());
        }

        const fetchReview = async () => {
            try {
                const response = await axios.get('http://127.0.0.1:8000/review');
                if (response.data.review && response.data.timestamp) {
                    // 只有当是当前查询且review是在查询之后生成的才更新
                    if (query === currentQuery && 
                        response.data.timestamp > lastReviewTimestamp) {
                        setReview(response.data.review);
                        setLoading(false);
                    }
                }
            } catch (err) {
                if (query === currentQuery) {
                    setError('Failed to fetch review');
                    setLoading(false);
                }
            }
        };

        // 立即执行一次
        fetchReview();
        
        // 设置轮询
        const interval = setInterval(fetchReview, 10000);
        
        return () => clearInterval(interval);
        
    }, [query, currentQuery, lastReviewTimestamp]);

    if (loading) {
        return (
            <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column',
                alignItems: 'center', 
                justifyContent: 'center', 
                p: 3 
            }}>
                <CircularProgress sx={{ mb: 2 }} />
                <Typography>
                    Generating Literature Review for "{query}"...
                </Typography>
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ p: 3 }}>
                <Typography color="error">{error}</Typography>
            </Box>
        );
    }

    if (!review) {
        return (
            <Box sx={{ p: 3 }}>
                <Typography>
                    Waiting for Literature Review generation to start...
                </Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3, maxHeight: '100%', overflow: 'auto' }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
                Literature Review for: {query}
            </Typography>
            <Typography variant="body1" 
                sx={{ 
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'serif',
                    lineHeight: 1.8 
                }}
            >
                {review}
            </Typography>
        </Box>
    );
};

export default LiteratureReview; 