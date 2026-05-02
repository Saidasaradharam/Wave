import { useState, useEffect, useRef } from 'react';
import { Bell, UserCircle, LogOut, Check } from 'lucide-react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import api from '../services/api';
import toast from 'react-hot-toast';

function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const dropdownRef = useRef(null);

  useEffect(() => {
    fetchNotifications();
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchNotifications = async () => {
    try {
      const res = await api.get('/notifications');
      setNotifications(res.data);
      setUnreadCount(res.data.filter(n => !n.read).length);
    } catch (err) {
      console.error(err);
    }
  };

  const markAsRead = async (id, e) => {
    e.stopPropagation();
    try {
      await api.put(`/notifications/${id}/read`);
      setNotifications(notifications.map(n => n.id === id ? { ...n, read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      toast.error('Failed to mark notification');
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Accessibility: aria-label and aria-expanded for screen readers */}
      <button 
        id="notification-bell-btn"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={`Notifications${unreadCount > 0 ? `, ${unreadCount} unread` : ''}`}
        aria-expanded={isOpen}
        aria-haspopup="true"
        className="relative p-2 text-slate-500 hover:bg-slate-100 rounded-full transition-colors"
      >
        <Bell className="w-6 h-6" aria-hidden="true" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 flex h-3 w-3" aria-hidden="true">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500"></span>
          </span>
        )}
      </button>

      {isOpen && (
        <div
          id="notification-dropdown"
          role="dialog"
          aria-modal="true"
          aria-label="Notifications panel"
          className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden z-50"
        >
          <div className="p-4 border-b border-slate-100 bg-slate-50">
            <h3 className="font-bold text-slate-800" id="notification-title">Notifications</h3>
          </div>
          <div className="max-h-96 overflow-y-auto" role="list" aria-labelledby="notification-title">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-slate-500" role="listitem">No notifications</div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif.id}
                  role="listitem"
                  className={`p-4 border-b border-slate-50 flex items-start justify-between ${notif.read ? 'bg-white opacity-60' : 'bg-indigo-50/30'}`}
                >
                  <p className="text-sm text-slate-700">{notif.content}</p>
                  {!notif.read && (
                    <button 
                      onClick={(e) => markAsRead(notif.id, e)}
                      className="p-1 hover:bg-indigo-100 rounded-full text-indigo-600 transition-colors"
                      aria-label={`Mark notification as read: ${notif.content}`}
                      title="Mark as read"
                    >
                      <Check className="w-4 h-4" aria-hidden="true" />
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Layout({ children, onLogout }) {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50 to-purple-50">
      {/* Accessibility: Skip to main content link for keyboard users */}
      <a href="#main-content" className="skip-to-content">
        Skip to main content
      </a>

      <nav
        className="bg-white/80 backdrop-blur-md border-b border-white/20 shadow-sm sticky top-0 z-40"
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <span className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  Wave
                </span>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link
                  id="nav-projects"
                  to="/projects"
                  aria-current={location.pathname.startsWith('/projects') ? 'page' : undefined}
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    location.pathname.startsWith('/projects')
                      ? 'border-indigo-500 text-slate-900'
                      : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'
                  }`}
                >
                  Projects
                </Link>
                <Link
                  id="nav-dashboard"
                  to="/dashboard"
                  aria-current={location.pathname === '/dashboard' ? 'page' : undefined}
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    location.pathname === '/dashboard'
                      ? 'border-indigo-500 text-slate-900'
                      : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'
                  }`}
                >
                  My Tasks
                </Link>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <NotificationBell />
              <button
                id="logout-btn"
                onClick={onLogout}
                className="flex items-center space-x-1 text-slate-500 hover:text-rose-600 transition-colors"
                aria-label="Log out"
                title="Logout"
              >
                <LogOut className="w-5 h-5" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Accessibility: Main content landmark with id for skip link */}
      <main id="main-content" className="p-8" role="main">
        {children}
      </main>
    </div>
  );
}

export default Layout;
