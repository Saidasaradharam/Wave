import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import api from '../services/api';
import { ClipboardList, ArrowRight, Filter, Inbox } from 'lucide-react';

export default function Dashboard() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchMyTasks();
  }, []);

  const fetchMyTasks = async () => {
    try {
      const res = await api.get('/tasks/assigned-to-me');
      setTasks(res.data);
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error('Session expired. Please log in again.');
        navigate('/login');
      } else {
        toast.error('Failed to load tasks');
      }
    } finally {
      setLoading(false);
    }
  };

  const filteredTasks = statusFilter === 'all'
    ? tasks
    : tasks.filter(t => t.status === statusFilter);

  // Group tasks by project
  const tasksByProject = filteredTasks.reduce((groups, task) => {
    const projectName = task.project_id ? `Project #${task.project_id}` : 'Unassigned';
    if (!groups[projectName]) {
      groups[projectName] = { id: task.project_id, tasks: [] };
    }
    groups[projectName].tasks.push(task);
    return groups;
  }, {});

  const statusConfig = {
    todo: { label: 'To Do', color: 'bg-slate-100 text-slate-700', dot: 'bg-slate-400' },
    in_progress: { label: 'In Progress', color: 'bg-indigo-100 text-indigo-700', dot: 'bg-indigo-500' },
    done: { label: 'Done', color: 'bg-emerald-100 text-emerald-700', dot: 'bg-emerald-500' },
  };

  const priorityConfig = {
    high: 'bg-red-100 text-red-700',
    medium: 'bg-amber-100 text-amber-700',
    low: 'bg-emerald-100 text-emerald-700',
  };

  const counts = {
    all: tasks.length,
    todo: tasks.filter(t => t.status === 'todo').length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
    done: tasks.filter(t => t.status === 'done').length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-6rem)]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-200 border-t-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2.5 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-xl shadow-md">
            <ClipboardList className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-slate-800">My Tasks</h1>
        </div>
        <p className="text-slate-500 ml-14">Tasks assigned to you across all projects</p>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center space-x-2 mb-6 bg-white/60 backdrop-blur-md p-2 rounded-2xl border border-white/50 shadow-sm" role="tablist" aria-label="Filter tasks by status">
        <Filter className="w-4 h-4 text-slate-400 ml-2" />
        {[
          { key: 'all', label: 'All' },
          { key: 'todo', label: 'To Do' },
          { key: 'in_progress', label: 'In Progress' },
          { key: 'done', label: 'Done' },
        ].map(tab => (
          <button
            key={tab.key}
            role="tab"
            aria-selected={statusFilter === tab.key}
            onClick={() => setStatusFilter(tab.key)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              statusFilter === tab.key
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                : 'text-slate-500 hover:bg-slate-100'
            }`}
          >
            {tab.label}
            <span className={`ml-2 px-1.5 py-0.5 rounded-full text-xs ${
              statusFilter === tab.key ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-600'
            }`}>
              {counts[tab.key]}
            </span>
          </button>
        ))}
      </div>

      {/* Empty state */}
      {filteredTasks.length === 0 && (
        <div className="bg-white/60 backdrop-blur-md rounded-2xl border border-white/50 p-16 text-center shadow-sm">
          <Inbox className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-slate-700 mb-2">
            {statusFilter === 'all' ? 'No tasks assigned to you yet' : `No ${statusConfig[statusFilter]?.label || ''} tasks`}
          </h3>
          <p className="text-slate-500 mb-6">
            Tasks are created inside projects. Go to a project to get started.
          </p>
          <button
            onClick={() => navigate('/projects')}
            className="inline-flex items-center space-x-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-xl font-medium shadow-md hover:shadow-lg transition-all"
          >
            <span>Go to Projects</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Tasks grouped by project */}
      <div className="space-y-6">
        {Object.entries(tasksByProject).map(([projectName, group]) => (
          <div key={projectName} className="bg-white/60 backdrop-blur-md rounded-2xl border border-white/50 shadow-sm overflow-hidden">
            {/* Project header */}
            <button
              onClick={() => navigate(`/projects/${group.id}`)}
              className="w-full flex items-center justify-between p-5 border-b border-slate-100 hover:bg-indigo-50/50 transition-colors group"
              aria-label={`Go to ${projectName}`}
            >
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500"></div>
                <h2 className="font-bold text-slate-800">{projectName}</h2>
                <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">{group.tasks.length} tasks</span>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-500 transition-colors" />
            </button>

            {/* Task list */}
            <div className="divide-y divide-slate-50">
              {group.tasks.map(task => (
                <button
                  key={task.id}
                  onClick={() => navigate(`/projects/${task.project_id}`)}
                  className="w-full flex items-center justify-between p-4 hover:bg-slate-50/80 transition-colors text-left group"
                  aria-label={`View task: ${task.title}`}
                >
                  <div className="flex items-center space-x-4 min-w-0 flex-1">
                    {/* Status dot */}
                    <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${statusConfig[task.status]?.dot || 'bg-slate-400'}`}></div>

                    {/* Title & description */}
                    <div className="min-w-0 flex-1">
                      <h3 className="font-semibold text-slate-800 truncate group-hover:text-indigo-600 transition-colors">{task.title}</h3>
                      {task.description && (
                        <p className="text-sm text-slate-500 truncate mt-0.5">{task.description}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 flex-shrink-0 ml-4">
                    {/* Priority badge */}
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${priorityConfig[task.priority] || ''}`}>
                      {task.priority}
                    </span>

                    {/* Status badge */}
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${statusConfig[task.status]?.color || ''}`}>
                      {statusConfig[task.status]?.label || task.status}
                    </span>

                    {/* Due date */}
                    {task.due_date && (
                      <span className="text-xs text-slate-400">
                        {new Date(task.due_date).toLocaleDateString()}
                      </span>
                    )}

                    <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-indigo-500 transition-colors" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
