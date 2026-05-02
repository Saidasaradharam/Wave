import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../services/api';
import { toast } from 'react-hot-toast';
import { Plus, Users, ShieldCheck, Settings } from 'lucide-react';
import KanbanBoard from '../components/KanbanBoard';
import TaskDetailModal from '../components/TaskDetailModal';

function ProjectDetail() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);

  useEffect(() => {
    fetchProjectDetails();
  }, [id]);

  const fetchProjectDetails = async () => {
    try {
      const [projRes, tasksRes] = await Promise.all([
        api.get(`/projects/${id}`),
        api.get(`/projects/${id}/tasks`)
      ]);
      setProject(projRes.data);
      setTasks(tasksRes.data);
    } catch (error) {
      toast.error('Failed to load project details');
    } finally {
      setLoading(false);
    }
  };

  const handleTaskMove = async (taskId, newStatus, newPosition, oldStatus, oldPosition) => {
    const updatedTasks = Array.from(tasks);
    const taskIndex = updatedTasks.findIndex(t => t.id === taskId);
    const movedTask = { ...updatedTasks[taskIndex], status: newStatus, position: newPosition };
    updatedTasks[taskIndex] = movedTask;
    setTasks(updatedTasks);

    try {
      await api.put(`/tasks/${taskId}/move`, {
        new_status: newStatus,
        new_position: newPosition
      });
    } catch (error) {
      toast.error('Failed to move task');
      fetchProjectDetails();
    }
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
      await api.post(`/projects/${id}/tasks`, {
        title: formData.get('title'),
        description: formData.get('description'),
        priority: formData.get('priority'),
        status: 'todo'
      });
      toast.success('Task created successfully');
      setShowTaskModal(false);
      fetchProjectDetails();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create task');
    }
  };

  const handleInviteMember = async (e) => {
    e.preventDefault();
    const email = e.target.email.value;
    try {
      await api.post(`/projects/${id}/invite?email=${encodeURIComponent(email)}`);
      toast.success('User invited successfully');
      setShowInviteModal(false);
      fetchProjectDetails();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to invite user');
    }
  };

  const handleTaskClick = (task) => {
    setSelectedTask(task);
  };

  if (loading) return (
    <div className="flex items-center justify-center p-12 h-[calc(100vh-4rem)]">
      <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-200 border-t-indigo-600"></div>
    </div>
  );

  if (!project) return <div className="text-center p-12 text-slate-500">Project not found</div>;

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col space-y-6 animate-fade-in">
      <div className="flex justify-between items-center bg-white/60 p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <h1 className="text-3xl font-bold text-slate-800">{project.name}</h1>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${project.visibility === 'public' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
              {project.visibility}
            </span>
          </div>
          <p className="text-slate-600">{project.description}</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex -space-x-2 mr-4">
            {project.members?.slice(0, 5).map((member) => (
              <div key={member.id} title={member.user.name} className="w-8 h-8 rounded-full border-2 border-white bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-xs shadow-sm">
                {member.user.name.charAt(0).toUpperCase()}
              </div>
            ))}
            {project.members?.length > 5 && (
              <div className="w-8 h-8 rounded-full border-2 border-white bg-slate-200 flex items-center justify-center text-slate-600 font-bold text-xs shadow-sm">
                +{project.members.length - 5}
              </div>
            )}
          </div>
          <button 
            onClick={() => setShowInviteModal(true)}
            className="p-2 bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-xl transition-colors"
            title="Invite Member"
          >
            <Users className="w-5 h-5" />
          </button>
          <button 
            onClick={() => setShowTaskModal(true)}
            className="flex items-center space-x-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-2 rounded-xl font-medium shadow-md hover:shadow-lg transition-all"
          >
            <Plus className="w-5 h-5" />
            <span>Add Task</span>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <KanbanBoard tasks={tasks} onTaskMove={handleTaskMove} onTaskClick={handleTaskClick} />
      </div>

      {showTaskModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full border border-slate-100 transform transition-all">
            <h2 className="text-2xl font-bold text-slate-800 mb-6">Create New Task</h2>
            <form onSubmit={handleCreateTask} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Task Title</label>
                <input 
                  type="text" 
                  name="title" 
                  required 
                  className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                <textarea 
                  name="description" 
                  rows="3"
                  className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                ></textarea>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Priority</label>
                <select 
                  name="priority"
                  className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div className="flex space-x-3 pt-4">
                <button 
                  type="button" 
                  onClick={() => setShowTaskModal(false)}
                  className="flex-1 px-4 py-2 bg-slate-100 text-slate-700 rounded-xl font-medium hover:bg-slate-200 transition-colors"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
                >
                  Create Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showInviteModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full border border-slate-100 transform transition-all">
            <h2 className="text-2xl font-bold text-slate-800 mb-6">Invite Member</h2>
            <form onSubmit={handleInviteMember} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
                <input 
                  type="email" 
                  name="email" 
                  required 
                  placeholder="colleague@example.com"
                  className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                />
              </div>
              <div className="flex space-x-3 pt-4">
                <button 
                  type="button" 
                  onClick={() => setShowInviteModal(false)}
                  className="flex-1 px-4 py-2 bg-slate-100 text-slate-700 rounded-xl font-medium hover:bg-slate-200 transition-colors"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
                >
                  Send Invite
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedTask && (
        <TaskDetailModal 
          task={selectedTask} 
          onClose={() => setSelectedTask(null)}
          onUpdate={fetchProjectDetails}
        />
      )}
    </div>
  );
}

export default ProjectDetail;
