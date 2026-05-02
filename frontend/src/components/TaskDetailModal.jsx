import { useState, useEffect } from 'react';
import { X, MessageSquare, Send, Paperclip } from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';

function TaskDetailModal({ task, members = [], onClose, onUpdate }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);

  const handleUpdate = (field, value) => {
    onUpdate(task.id, { [field]: value });
  };

  useEffect(() => {
    fetchComments();
  }, [task.id]);

  const fetchComments = async () => {
    try {
      const res = await api.get(`/tasks/${task.id}/comments`);
      setComments(res.data);
    } catch (err) {
      toast.error('Failed to load comments');
    } finally {
      setLoading(false);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    try {
      await api.post(`/tasks/${task.id}/comments`, { content: newComment });
      setNewComment('');
      fetchComments();
    } catch (err) {
      toast.error('Failed to add comment');
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" role="dialog" aria-modal="true" aria-labelledby="task-detail-title">
      <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col border border-slate-100 overflow-hidden">
        
        {/* Header */}
        <div className="p-6 border-b border-slate-100 flex justify-between items-start bg-slate-50">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <select
                value={task.priority}
                onChange={(e) => handleUpdate('priority', e.target.value)}
                className={`px-2 py-1 rounded-full text-xs font-medium uppercase tracking-wider border-none focus:ring-2 focus:ring-indigo-500 cursor-pointer ${
                  task.priority === 'high' ? 'bg-rose-100 text-rose-700' :
                  task.priority === 'medium' ? 'bg-amber-100 text-amber-700' :
                  'bg-slate-200 text-slate-700'
                }`}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
              <select
                value={task.status}
                onChange={(e) => handleUpdate('status', e.target.value)}
                className="text-slate-500 text-sm bg-transparent border-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
              >
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="done">Done</option>
              </select>
            </div>
            <h2 id="task-detail-title" className="text-2xl font-bold text-slate-800">{task.title}</h2>
          </div>
          <button id="task-detail-close-btn" onClick={onClose} className="p-2 hover:bg-slate-200 rounded-full text-slate-500 transition-colors" aria-label="Close task details">
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 grid grid-cols-3 gap-8">
          <div className="col-span-2 space-y-6">
            <div>
              <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-2">Description</h3>
              <div className="bg-slate-50 p-4 rounded-xl text-slate-700 whitespace-pre-wrap text-sm border border-slate-100 min-h-[100px]">
                {task.description || <span className="text-slate-400 italic">No description provided.</span>}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-4 flex items-center">
                <MessageSquare className="w-4 h-4 mr-2" /> Comments
              </h3>
              
              <div className="space-y-4 mb-4">
                {loading ? (
                  <div className="animate-pulse flex space-x-4">
                    <div className="rounded-full bg-slate-200 h-10 w-10"></div>
                    <div className="flex-1 space-y-2 py-1">
                      <div className="h-4 bg-slate-200 rounded w-3/4"></div>
                      <div className="h-4 bg-slate-200 rounded w-1/2"></div>
                    </div>
                  </div>
                ) : comments.length === 0 ? (
                  <p className="text-sm text-slate-500 italic">No comments yet. Be the first to start the discussion!</p>
                ) : (
                  comments.map(comment => (
                    <div key={comment.id} className="flex space-x-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex-shrink-0 flex items-center justify-center text-white font-bold text-xs">
                        {comment.user.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 bg-slate-50 p-3 rounded-2xl rounded-tl-none border border-slate-100">
                        <div className="flex justify-between items-baseline mb-1">
                          <span className="font-semibold text-sm text-slate-800">{comment.user.name}</span>
                          <span className="text-xs text-slate-400">{new Date(comment.created_at).toLocaleString()}</span>
                        </div>
                        <p className="text-sm text-slate-700">{comment.content}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>

              <form onSubmit={handleAddComment} className="relative">
                <textarea
                  id="task-comment-input"
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Add a comment... Use @ to mention someone"
                  aria-label="Add a comment to this task"
                  className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all pr-12 text-sm min-h-[80px]"
                />
                <button 
                  id="task-comment-submit-btn"
                  type="submit"
                  disabled={!newComment.trim()}
                  className="absolute bottom-3 right-3 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:hover:bg-indigo-600 transition-colors"
                  aria-label="Submit comment"
                >
                  <Send className="w-4 h-4" aria-hidden="true" />
                </button>
              </form>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <div>
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Details</h3>
              <div className="bg-slate-50 p-4 rounded-xl space-y-4 border border-slate-100 text-sm">
                <div>
                  <span className="text-slate-500 block mb-1">Assignee</span>
                  <select
                    value={task.assignee_id || ''}
                    onChange={(e) => handleUpdate('assignee_id', e.target.value ? parseInt(e.target.value) : null)}
                    className="w-full bg-transparent border-none p-0 font-medium text-slate-700 focus:ring-0 cursor-pointer"
                  >
                    <option value="">Unassigned</option>
                    {members.map(member => (
                      <option key={member.user.id} value={member.user.id}>
                        {member.user.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <span className="text-slate-500 block mb-1">Reporter</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center font-bold text-xs">
                      {task.created_by.name.charAt(0).toUpperCase()}
                    </div>
                    <span className="font-medium text-slate-700">{task.created_by.name}</span>
                  </div>
                </div>
                {task.due_date && (
                  <div>
                    <span className="text-slate-500 block mb-1">Due Date</span>
                    <span className="font-medium text-slate-700">{new Date(task.due_date).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TaskDetailModal;
