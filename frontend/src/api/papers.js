import axios from 'axios';
import axiosInstance from '../utils/axios';

export const searchPapers = async (query) => {
  const response = await axios.get('/api/v1/papers/search', {
    params: { query }
  });
  return response.data;
};

export const fetchCitationNetwork = async (query, topK) => {
    try {
        const response = await axios.get('http://127.0.0.1:8000/citation_network/' + query, {
            params: { top_k: topK }
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching citation network:', error);
        throw error;
    }
};

export const fetchPaperSubNetwork = async (paperId, signal) => {
    try {
        console.log('Sending request to fetch sub-network');
        const response = await axiosInstance.get(`http://127.0.0.1:8000/paper_network/${paperId}`, {
            timeout: 0,
            signal,
            validateStatus: function (status) {
                return status >= 200 && status < 300;
            },
        });
        console.log('Received response:', response.data);
        return response.data;
    } catch (error) {
        if (axios.isCancel(error)) {
            console.log('Request canceled:', error.message);
            throw new Error('Request canceled');
        }
        console.error('Error fetching paper sub-network:', error);
        throw error;
    }
}; 