import { useState, useEffect } from 'react';
import TaskBoard from '../components/TaskBoard';
import { getTasks, getActivity, getUsers } from '../services/api';

export default function Dashboard({ onLogout }) {
  const [tasks, setTasks] = useState([]);
  const [activity, setActivity] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [tasksRes, actRes, usersRes] = await Promise.all([
        getTasks(), getActivity(), getUsers()
      ]);
      setTasks(tasksRes);
      setActivity(actRes);
      setUsers(usersRes);
    } catch (error) {
      console.error("Error fetching dashboard data", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // In a real app, we'd use WebSockets for real-time updates.
    // For this, we'll poll every 30 seconds.
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-200 border-t-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50 to-purple-50 p-6 md:p-8">
      <div className="max-w-[1400px] mx-auto h-full flex flex-col">
        {/* Header with gradient */}
        <header className="mb-8 flex justify-between items-center bg-white/60 backdrop-blur-md p-4 rounded-2xl shadow-sm border border-white/50">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-1">
              Wave
            </h1>
            <p className="text-slate-600 text-sm font-medium">Built with Antigravity AI</p>
          </div>
          <button 
            onClick={onLogout}
            className="px-4 py-2 bg-slate-100 hover:bg-red-50 hover:text-red-600 text-slate-700 rounded-lg text-sm font-semibold transition-colors"
          >
            Logout
          </button>
        </header>
        
        {/* Main content grid */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Kanban Board Area */}
          <main className="lg:col-span-3 glassmorphism rounded-3xl p-6 h-[calc(100vh-200px)] overflow-hidden">
            <TaskBoard tasks={tasks} onTaskUpdate={fetchData} />
          </main>

          {/* Sidebar Area */}
          <aside className="space-y-6">
            {/* Team Members */}
            <div className="glassmorphism rounded-2xl p-6 border-t-4 border-t-indigo-500">
              <h3 className="font-bold text-slate-800 mb-4 flex items-center">
                <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2"></span>
                Team Members
              </h3>
              <ul className="space-y-3">
                {users.map(user => (
                  <li key={user.id} className="flex items-center text-sm">
                    <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold mr-3">
                      {user.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="font-medium text-slate-700">{user.name}</p>
                      <p className="text-xs text-slate-500">{user.role}</p>
                    </div>
                    <span className="ml-auto w-2 h-2 rounded-full bg-emerald-400"></span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Activity Feed */}
            <div className="glassmorphism rounded-2xl p-6 border-t-4 border-t-purple-500">
              <h3 className="font-bold text-slate-800 mb-4">Recent Activity</h3>
              <div className="space-y-4 max-h-64 overflow-y-auto pr-2">
                {activity.length === 0 ? (
                  <p className="text-sm text-slate-500">No recent activity</p>
                ) : (
                  activity.map((item, i) => (
                    <div key={i} className="flex gap-3 text-sm border-l-2 border-slate-200 pl-3 py-1">
                      <div>
                        <p className="text-slate-700 font-medium">{item.description}</p>
                        <p className="text-xs text-slate-400 mt-1">
                          {new Date(item.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
