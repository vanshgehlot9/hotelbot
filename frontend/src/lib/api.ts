import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const path = window.location.pathname;
    let token = null;
    
    if (path.startsWith('/superadmin')) {
      token = localStorage.getItem('superadmin_token');
    } else if (path.startsWith('/tenant')) {
      token = localStorage.getItem('tenant_token');
    } else if (path.startsWith('/staff')) {
      token = localStorage.getItem('staff_token');
    } else {
      // Fallback for global or mixed components
      token = localStorage.getItem('access_token');
    }
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export default api;
