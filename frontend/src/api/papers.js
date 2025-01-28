import axios from '../utils/axios';

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