import { useState, useEffect } from 'react';
import AuthForms from './components/AuthForms';
import Dashboard from './pages/Dashboard';
import FloatingFooter from './components/FloatingFooter';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simple check if token exists. In real app, validate token with backend.
    const token = localStorage.getItem('token');
    if (token) {
      setUser({ authenticated: true });
    }
    setLoading(false);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-200 border-t-indigo-600"></div>
      </div>
    );
  }

  return (
    <>
      {user ? (
        <Dashboard onLogout={handleLogout} />
      ) : (
        <AuthForms onAuthSuccess={(userData) => setUser(userData)} />
      )}
      <FloatingFooter />
    </>
  );
}

export default App;
