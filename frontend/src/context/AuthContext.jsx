import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('qm_token'));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          throw new Error('Invalid token');
        }
        const data = await res.json();
        if (data && data.id && data.email) {
          setUser(data);
        } else {
          throw new Error('Invalid response');
        }
      } catch {
        localStorage.removeItem('qm_token');
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, [token]);

  async function login(email, password) {
    const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok || !data.access_token) {
      throw new Error(data.error || data.detail || 'Login failed');
    }
    const t = data.access_token;
    setToken(t);
    localStorage.setItem('qm_token', t);
    const me = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/me`, {
      headers: { Authorization: `Bearer ${t}` },
    });
    const meData = await me.json();
    if (meData && (meData.id || meData.email)) {
      setUser(meData);
    }
  }

  async function register(email, password) {
    const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok || !data.access_token) {
      throw new Error(data.error || data.detail || 'Registration failed');
    }
    const t = data.access_token;
    setToken(t);
    localStorage.setItem('qm_token', t);
    const me = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/me`, {
      headers: { Authorization: `Bearer ${t}` },
    });
    const meData = await me.json();
    if (meData && (meData.id || meData.email)) {
      setUser(meData);
    }
  }

  async function googleLogin(idToken) {
    const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_token: idToken }),
    });
    const data = await res.json();
    if (!res.ok || !data.access_token) {
      throw new Error(data.error || data.detail || 'Google login failed');
    }
    const t = data.access_token;
    setToken(t);
    localStorage.setItem('qm_token', t);
    const me = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/me`, {
      headers: { Authorization: `Bearer ${t}` },
    });
    const meData = await me.json();
    if (meData && (meData.id || meData.email)) {
      setUser(meData);
    }
  }

  function logout() {
    setToken(null);
    setUser(null);
    localStorage.removeItem('qm_token');
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, googleLogin, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
