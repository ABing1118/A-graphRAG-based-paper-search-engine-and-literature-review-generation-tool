import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';  // 支持 GitHub Flavored Markdown
import rehypeHighlight from 'rehype-highlight';  // 代码高亮

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
            
            {/* 使用 ReactMarkdown 渲染 Markdown 格式 */}
            <Box sx={{ 
                fontFamily: 'serif',
                lineHeight: 1.8,
                '& h1, & h2, & h3, & h4, & h5, & h6': {
                    fontWeight: 'bold',
                    mt: 3,
                    mb: 2
                },
                '& h1': { fontSize: '2rem' },
                '& h2': { fontSize: '1.8rem' },
                '& h3': { fontSize: '1.6rem' },
                '& h4': { fontSize: '1.4rem' },
                '& h5': { fontSize: '1.2rem' },
                '& h6': { fontSize: '1.1rem' },
                '& p': { mb: 2 },
                '& ul, & ol': { ml: 3, mb: 2 },
                '& blockquote': {
                    borderLeft: '4px solid #ccc',
                    pl: 2,
                    fontStyle: 'italic'
                },
                '& code': {
                    fontFamily: 'monospace',
                    backgroundColor: '#f5f5f5',
                    p: 0.5,
                    borderRadius: 1
                },
                '& pre': {
                    backgroundColor: '#f5f5f5',
                    p: 2,
                    borderRadius: 1,
                    overflow: 'auto'
                },
                '& strong': {
                    fontWeight: 'bold'
                },
                '& em': {
                    fontStyle: 'italic'
                }
            }}>
                <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeHighlight]}
                >
                    {review}
                </ReactMarkdown>
            </Box>
        </Box>
    );
};

export default LiteratureReview; 