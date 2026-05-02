import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { login, register } from '../services/api';

export default function AuthForms({ isLoginRoute }) {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const validateForm = () => {
    if (!email || !/\S+@\S+\.\S+/.test(email)) {
      setError('Please enter a valid email address');
      return false;
    }
    if (!password || password.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }
    if (!isLoginRoute && (!name || name.trim().length < 2)) {
      setError('Name must be at least 2 characters long');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    
    setError('');
    setLoading(true);

    try {
      if (isLoginRoute) {
        const data = await login(email, password);
        localStorage.setItem('token', data.access_token);
        toast.success('Successfully logged in!');
        navigate('/tasks');
      } else {
        const data = await register(name, email, password);
        const loginData = await login(email, password);
        localStorage.setItem('token', loginData.access_token);
        toast.success('Account created successfully!');
        navigate('/tasks');
      }
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Authentication failed. Please try again.';
      setError(errMsg);
      toast.error(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const clearError = () => {
    if (error) setError('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50 to-purple-50 p-8 flex items-center justify-center">
      <main role="main" aria-label="Authentication form" className="glassmorphism rounded-2xl p-8 w-full max-w-md">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-6 text-center">
          {isLoginRoute ? 'Welcome Back' : 'Create Account'}
        </h1>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm font-medium" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} aria-labelledby="form-title" className="space-y-4">
          {!isLoginRoute && (
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-1">
                Name
              </label>
              <input
                id="name"
                type="text"
                required
                aria-required="true"
                value={name}
                onChange={(e) => { setName(e.target.value); clearError(); }}
                className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
              />
            </div>
          )}
          
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              aria-required="true"
              value={email}
              onChange={(e) => { setEmail(e.target.value); clearError(); }}
              className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              aria-required="true"
              value={password}
              onChange={(e) => { setPassword(e.target.value); clearError(); }}
              className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            aria-label={isLoginRoute ? 'Submit login form' : 'Submit registration form'}
            className="w-full flex justify-center items-center bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-50"
          >
            {loading ? (
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : null}
            {loading ? 'Processing...' : (isLoginRoute ? 'Log In' : 'Sign Up')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <Link
            to={isLoginRoute ? '/register' : '/login'}
            onClick={clearError}
            className="text-sm font-medium text-indigo-600 hover:text-indigo-800 transition-colors"
          >
            {isLoginRoute ? "Don't have an account? Sign up" : "Already have an account? Log in"}
          </Link>
        </div>
      </main>
    </div>
  );
}
