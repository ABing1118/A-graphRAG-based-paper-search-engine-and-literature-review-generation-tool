import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';
import axios from 'axios';

const LiteratureReview = () => {
    const [review, setReview] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchReview = async () => {
            try {
                const response = await axios.get('http://127.0.0.1:8000/review');
                if (response.data.review) {
                    setReview(response.data.review);
                }
            } catch (err) {
                setError('Failed to fetch review');
                console.error('Error fetching review:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchReview();
        // 可以设置定期轮询
        const interval = setInterval(fetchReview, 10000); // 每10秒检查一次

        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
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
                <Typography>No review available yet...</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3, maxHeight: '100%', overflow: 'auto' }}>
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