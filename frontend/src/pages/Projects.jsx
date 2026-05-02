import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { toast } from 'react-hot-toast';
import { Plus, Users, ShieldCheck } from 'lucide-react';

function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await api.get('/projects');
      setProjects(response.data);
    } catch (error) {
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
      await api.post('/projects', {
        name: formData.get('name'),
        description: formData.get('description'),
        visibility: formData.get('visibility'),
      });
      toast.success('Project created successfully!');
      setShowCreateModal(false);
      fetchProjects();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create project');
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center p-12">
      <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-200 border-t-indigo-600"></div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-2">
            Projects
          </h1>
          <p className="text-slate-600">Manage your team projects and collaborations.</p>
        </div>
        <button 
          id="create-project-btn"
          onClick={() => setShowCreateModal(true)}
          className="flex items-center space-x-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200"
          aria-label="Create a new project"
        >
          <Plus className="w-5 h-5" />
          <span>New Project</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map((project) => (
          <div 
            key={project.id} 
            onClick={() => navigate(`/projects/${project.id}`)}
            className="bg-white/80 backdrop-blur-md shadow-xl rounded-2xl border border-white/20 p-6 cursor-pointer hover:scale-105 hover:shadow-2xl transition-all duration-300"
          >
            <div className="flex justify-between items-start mb-4">
              <div className={`p-3 rounded-xl ${project.color || 'bg-indigo-500'} text-white`}>
                {project.visibility === 'public' ? <Users className="w-6 h-6" /> : <ShieldCheck className="w-6 h-6" />}
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${project.visibility === 'public' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                {project.visibility}
              </span>
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">{project.name}</h3>
            <p className="text-slate-600 text-sm line-clamp-2">{project.description || 'No description provided.'}</p>
          </div>
        ))}
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" role="dialog" aria-modal="true" aria-labelledby="create-project-title">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full border border-slate-100 transform transition-all">
            <h2 id="create-project-title" className="text-2xl font-bold text-slate-800 mb-6">Create New Project</h2>
            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Project Name</label>
                <input 
                  type="text" 
                  name="name" 
                  id="project-name-input"
                  required 
                  aria-required="true"
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
                <label className="block text-sm font-medium text-slate-700 mb-1">Visibility</label>
                <select 
                  name="visibility"
                  className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                >
                  <option value="private">Private (Invite Only)</option>
                  <option value="public">Public (Anyone can join)</option>
                </select>
              </div>
              <div className="flex space-x-3 pt-4">
                <button 
                  type="button" 
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 bg-slate-100 text-slate-700 rounded-xl font-medium hover:bg-slate-200 transition-colors"
                >
                  Cancel
                </button>
                <button 
                  id="create-project-submit-btn"
                  type="submit"
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Projects;
