import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { Calendar } from 'lucide-react';

const PRIORITY_COLORS = {
  low: 'bg-slate-100 text-slate-700',
  medium: 'bg-amber-100 text-amber-700',
  high: 'bg-rose-100 text-rose-700'
};

function KanbanBoard({ tasks, onTaskMove, onTaskClick }) {
  const columns = {
    todo: { id: 'todo', title: 'To Do', items: tasks.filter(t => t.status === 'todo').sort((a, b) => a.position - b.position) },
    in_progress: { id: 'in_progress', title: 'In Progress', items: tasks.filter(t => t.status === 'in_progress').sort((a, b) => a.position - b.position) },
    done: { id: 'done', title: 'Done', items: tasks.filter(t => t.status === 'done').sort((a, b) => a.position - b.position) }
  };

  const handleDragEnd = (result) => {
    if (!result.destination) return;
    const { source, destination, draggableId } = result;

    if (source.droppableId === destination.droppableId && source.index === destination.index) {
      return;
    }

    onTaskMove(parseInt(draggableId), destination.droppableId, destination.index, source.droppableId, source.index);
  };

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <div className="flex gap-6 overflow-x-auto pb-4 h-full" role="region" aria-label="Kanban board">
        {Object.values(columns).map(column => (
          <div key={column.id} className="flex-1 min-w-[320px] bg-slate-100/50 rounded-2xl p-4 flex flex-col max-h-[calc(100vh-14rem)]" role="region" aria-label={`${column.title} column, ${column.items.length} tasks`}>
            <h3 className="font-bold text-slate-700 mb-4 px-2 flex justify-between items-center">
              {column.title}
              <span className="bg-white/60 text-slate-500 text-xs px-2 py-1 rounded-full shadow-sm">
                {column.items.length}
              </span>
            </h3>
            
            <Droppable droppableId={column.id}>
              {(provided, snapshot) => (
                <div 
                  ref={provided.innerRef} 
                  {...provided.droppableProps}
                  className={`flex-1 overflow-y-auto space-y-3 p-2 rounded-xl transition-colors min-h-[150px] ${snapshot.isDraggingOver ? 'bg-indigo-50/50' : ''}`}
                >
                  {column.items.map((task, index) => (
                    <Draggable key={task.id} draggableId={task.id.toString()} index={index}>
                      {(provided, snapshot) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          onClick={() => onTaskClick(task)}
                          role="button"
                          aria-label={`Task: ${task.title}, Priority: ${task.priority}`}
                          tabIndex={0}
                          className={`bg-white p-4 rounded-xl shadow-sm border border-slate-100 cursor-pointer transition-all ${snapshot.isDragging ? 'shadow-xl rotate-2 scale-105 ring-2 ring-indigo-500 ring-offset-2 z-50' : 'hover:shadow-md hover:-translate-y-0.5'}`}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <span className={`text-xs font-medium px-2 py-1 rounded-full ${PRIORITY_COLORS[task.priority]}`}>
                              {task.priority}
                            </span>
                          </div>
                          <h4 className="font-bold text-slate-800 mb-1 leading-tight">{task.title}</h4>
                          {task.description && (
                            <p className="text-sm text-slate-500 line-clamp-2 mb-3">{task.description}</p>
                          )}
                          <div className="flex items-center justify-between text-xs text-slate-400 mt-2">
                            {task.due_date && (
                              <div className="flex items-center space-x-1">
                                <Calendar className="w-3 h-3" />
                                <span>{new Date(task.due_date).toLocaleDateString()}</span>
                              </div>
                            )}
                            {task.assignee && (
                              <div className="flex items-center space-x-1 ml-auto" title={`Assigned to ${task.assignee.name}`}>
                                <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-xs shadow-sm">
                                  {task.assignee.name.charAt(0).toUpperCase()}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </div>
        ))}
      </div>
    </DragDropContext>
  );
}

export default KanbanBoard;
