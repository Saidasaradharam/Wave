import { useState } from 'react';
import toast from 'react-hot-toast';
import { updateTask, createTask } from '../services/api';

export default function TaskBoard({ tasks, onTaskUpdate }) {
  const [isAdding, setIsAdding] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [addingTask, setAddingTask] = useState(false);
  
  const columns = [
    { id: 'todo', title: 'To Do', color: 'bg-slate-100' },
    { id: 'in_progress', title: 'In Progress', color: 'bg-indigo-50' },
    { id: 'done', title: 'Done', color: 'bg-emerald-50' }
  ];

  const handleMoveTask = async (task, newStatus) => {
    try {
      await updateTask(task.id, { status: newStatus });
      toast.success('Task updated successfully');
      onTaskUpdate();
    } catch (err) {
      toast.error('Failed to update task');
    }
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;
    setAddingTask(true);
    try {
      await createTask({ title: newTaskTitle, status: 'todo' });
      setNewTaskTitle('');
      setIsAdding(false);
      toast.success('Task created successfully');
      onTaskUpdate();
    } catch (err) {
      toast.error('Failed to create task');
    } finally {
      setAddingTask(false);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-full">
      {columns.map(col => (
        <div key={col.id} className={`${col.color} rounded-2xl p-4 flex flex-col h-full border border-slate-200/60`}>
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-bold text-slate-800 text-lg">{col.title}</h2>
            <span className="bg-white text-slate-600 px-2 py-1 rounded-full text-xs font-semibold shadow-sm">
              {tasks.filter(t => t.status === col.id).length}
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {tasks.filter(t => t.status === col.id).map(task => (
              <div 
                key={task.id} 
                className="glassmorphism p-4 rounded-xl cursor-pointer hover:scale-[1.02] transition-all duration-200"
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-slate-800">{task.title}</h3>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    task.priority === 'high' ? 'bg-red-100 text-red-700' :
                    task.priority === 'medium' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
                  }`}>
                    {task.priority}
                  </span>
                </div>
                <p className="text-sm text-slate-500 mb-4 line-clamp-2">{task.description || 'No description'}</p>
                
                <div className="flex justify-between items-center mt-2 pt-2 border-t border-slate-100">
                  <div className="text-xs text-slate-400">
                    {new Date(task.created_at).toLocaleDateString()}
                  </div>
                  <div className="flex space-x-2">
                    {col.id !== 'todo' && (
                      <button onClick={() => handleMoveTask(task, 'todo')} className="text-xs bg-slate-100 px-2 py-1 rounded hover:bg-slate-200">←</button>
                    )}
                    {col.id === 'todo' && (
                      <button onClick={() => handleMoveTask(task, 'in_progress')} className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded hover:bg-indigo-200">→</button>
                    )}
                    {col.id === 'in_progress' && (
                      <button onClick={() => handleMoveTask(task, 'done')} className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded hover:bg-emerald-200">✓</button>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {col.id === 'todo' && (
              isAdding ? (
                <form onSubmit={handleAddTask} className="mt-2 glassmorphism p-3 rounded-xl">
                  <input
                    autoFocus
                    className="w-full text-sm p-2 rounded border border-slate-200 mb-2 focus:ring-2 focus:ring-indigo-500 outline-none"
                    placeholder="Task title..."
                    value={newTaskTitle}
                    onChange={e => setNewTaskTitle(e.target.value)}
                    disabled={addingTask}
                  />
                  <div className="flex space-x-2">
                    <button disabled={addingTask} type="submit" className="flex-1 bg-indigo-600 text-white text-xs font-medium py-1.5 rounded disabled:opacity-50">
                      {addingTask ? 'Saving...' : 'Add'}
                    </button>
                    <button disabled={addingTask} type="button" onClick={() => setIsAdding(false)} className="flex-1 bg-slate-200 text-slate-700 text-xs font-medium py-1.5 rounded disabled:opacity-50">Cancel</button>
                  </div>
                </form>
              ) : (
                <button 
                  onClick={() => setIsAdding(true)}
                  className="w-full mt-2 py-2 text-sm font-medium text-slate-500 border-2 border-dashed border-slate-300 rounded-xl hover:text-indigo-600 hover:border-indigo-400 transition-colors"
                >
                  + Add Task
                </button>
              )
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
