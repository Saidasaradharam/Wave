import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import AuthForms from './components/AuthForms';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import Layout from './components/Layout';
import FloatingFooter from './components/FloatingFooter';

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

function App() {
  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  };

  return (
    <BrowserRouter>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/login" element={<AuthForms isLoginRoute={true} />} />
        <Route path="/register" element={<AuthForms isLoginRoute={false} />} />
        
        <Route path="/projects" element={
          <ProtectedRoute>
            <Layout onLogout={handleLogout}>
              <Projects />
            </Layout>
          </ProtectedRoute>
        } />
        
        <Route path="/projects/:id" element={
          <ProtectedRoute>
            <Layout onLogout={handleLogout}>
              <ProjectDetail />
            </Layout>
          </ProtectedRoute>
        } />

        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Layout onLogout={handleLogout}>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        } />

        {/* Redirect old /tasks URL */}
        <Route path="/tasks" element={<Navigate to="/dashboard" replace />} />

        <Route path="/" element={<Navigate to="/projects" replace />} />
      </Routes>
      <FloatingFooter />
    </BrowserRouter>
  );
}

export default App;
