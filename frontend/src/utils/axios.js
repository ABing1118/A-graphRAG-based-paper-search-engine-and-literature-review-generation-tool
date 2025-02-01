import axios from 'axios';

const instance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
});

// 添加请求拦截器来处理取消请求
instance.interceptors.request.use(function (config) {
  // 确保 signal 被正确传递
  if (config.signal) {
    const source = axios.CancelToken.source();
    config.cancelToken = source.token;
    config.signal.addEventListener('abort', () => {
      source.cancel('Request cancelled');
    });
  }
  return config;
});

export default instance; 