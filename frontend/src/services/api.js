import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('omni_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('omni_token');
      localStorage.removeItem('omni_user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// ---- Auth ----

export async function signup(email, password) {
  const { data } = await api.post('/auth/signup', { email, password });
  return data;
}

export async function login(email, password) {
  const { data } = await api.post('/auth/login', { email, password });
  return data;
}

// ---- Chat ----

export async function sendMessage(message, history = [], sessionId = null) {
  const { data } = await api.post('/chat', {
    message,
    history,
    session_id: sessionId,
  });
  return data;
}

// ---- Sessions ----

export async function fetchSessions() {
  const { data } = await api.get('/chat/sessions');
  return data;
}

export async function fetchSessionMessages(sessionId) {
  const { data } = await api.get(`/chat/sessions/${sessionId}/messages`);
  return data;
}

export async function deleteSession(sessionId) {
  const { data } = await api.delete(`/chat/sessions/${sessionId}`);
  return data;
}

// ---- Direct Emal Overrides ----

export async function sendDirectEmail(to, subject, body) {
  const { data } = await api.post('/send-email', { to, subject, body });
  return data;
}

export async function draftDirectEmail(to, subject, body) {
  const { data } = await api.post('/draft-email', { to, subject, body });
  return data;
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
}

// ---- Notifications ----

export async function fetchNotifications() {
  const { data } = await api.get('/notifications');
  return data;
}

export async function markNotificationsRead() {
  const { data } = await api.post('/notifications/read');
  return data;
}

export default api;
