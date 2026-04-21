import { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, signup as apiSignup } from '../services/api';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore session on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('omni_token');
    const savedUser = localStorage.getItem('omni_user');
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const saveSession = (data) => {
    const userData = { id: data.user_id, email: data.email };
    setToken(data.access_token);
    setUser(userData);
    localStorage.setItem('omni_token', data.access_token);
    localStorage.setItem('omni_user', JSON.stringify(userData));
  };

  const login = async (email, password) => {
    const data = await apiLogin(email, password);
    saveSession(data);
    return data;
  };

  const signup = async (email, password) => {
    const data = await apiSignup(email, password);
    saveSession(data);
    return data;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('omni_token');
    localStorage.removeItem('omni_user');
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, signup, logout, setOauthSession: saveSession, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
