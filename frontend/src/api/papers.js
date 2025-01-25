import axios from '../utils/axios';

export const searchPapers = async (query) => {
  const response = await axios.get('/api/v1/papers/search', {
    params: { query }
  });
  return response.data;
}; 