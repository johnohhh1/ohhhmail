/**
 * Task Manager Component - Embedded in Open-WebUI
 * Shows tasks created from email processing
 */

import React, { useState, useEffect } from 'react';

interface Task {
  task_id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  created_at: string;
  due_date?: string;
  assignee?: string;
  email_id?: string;
  category?: string;
  tags: string[];
}

interface TaskManagerProps {
  className?: string;
}

export const TaskManager: React.FC<TaskManagerProps> = ({ className = '' }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [filter, setFilter] = useState<'all' | 'pending' | 'in_progress' | 'completed'>('all');
  const [isLoading, setIsLoading] = useState(true);

  const fetchTasks = async () => {
    try {
      const response = await fetch(`/api/tasks?status=${filter}`);
      const data = await response.json();
      setTasks(data.tasks || []);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [filter]);

  const updateTaskStatus = async (taskId: string, newStatus: Task['status']) => {
    try {
      await fetch(`/api/tasks/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      fetchTasks();
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-100 text-red-700 border-red-300';
      case 'high':
        return 'bg-orange-100 text-orange-700 border-orange-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 border-yellow-300';
      case 'low':
        return 'bg-green-100 text-green-700 border-green-300';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'in_progress':
        return 'bg-blue-500';
      case 'pending':
        return 'bg-yellow-500';
      case 'cancelled':
        return 'bg-gray-500';
      default:
        return 'bg-gray-400';
    }
  };

  const isOverdue = (dueDate?: string) => {
    if (!dueDate) return false;
    return new Date(dueDate) < new Date();
  };

  return (
    <div className={`task-manager ${className}`}>
      {/* Header */}
      <div className="p-4 bg-gray-800 text-white">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold">Task Manager</h2>
          <div className="flex items-center gap-2">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="px-3 py-2 bg-gray-700 rounded text-sm"
            >
              <option value="all">All Tasks</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
            <button
              onClick={fetchTasks}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="flex h-full">
        {/* Task List */}
        <div className="w-96 border-r border-gray-300 overflow-y-auto bg-gray-50">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">Loading tasks...</div>
          ) : tasks.length === 0 ? (
            <div className="p-4 text-center text-gray-500">No tasks found</div>
          ) : (
            <div>
              {tasks.map((task) => (
                <button
                  key={task.task_id}
                  onClick={() => setSelectedTask(task)}
                  className={`w-full p-4 text-left border-b border-gray-200 hover:bg-gray-100 transition ${
                    selectedTask?.task_id === task.task_id
                      ? 'bg-blue-50 border-l-4 border-l-blue-500'
                      : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-3 h-3 rounded-full mt-1 ${getStatusColor(task.status)}`} />
                    <div className="flex-1">
                      <div className="font-semibold text-gray-800 mb-1">{task.title}</div>
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className={`text-xs px-2 py-1 rounded border ${getPriorityColor(
                            task.priority
                          )}`}
                        >
                          {task.priority}
                        </span>
                        {task.category && (
                          <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600">
                            {task.category}
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-gray-500">
                        Created: {new Date(task.created_at).toLocaleDateString()}
                      </div>
                      {task.due_date && (
                        <div
                          className={`text-xs ${
                            isOverdue(task.due_date) ? 'text-red-600 font-semibold' : 'text-gray-600'
                          }`}
                        >
                          Due: {new Date(task.due_date).toLocaleDateString()}
                          {isOverdue(task.due_date) && ' (OVERDUE)'}
                        </div>
                      )}
                      {task.assignee && (
                        <div className="text-xs text-gray-600 mt-1">👤 {task.assignee}</div>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Task Details */}
        <div className="flex-1 overflow-y-auto">
          {selectedTask ? (
            <div className="p-6">
              {/* Task Header */}
              <div className="mb-6 bg-white rounded-lg shadow p-4">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold mb-2">{selectedTask.title}</h3>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-sm px-3 py-1 rounded border ${getPriorityColor(
                          selectedTask.priority
                        )}`}
                      >
                        {selectedTask.priority} priority
                      </span>
                      <span className="text-sm px-3 py-1 rounded bg-gray-100 text-gray-700">
                        {selectedTask.status}
                      </span>
                    </div>
                  </div>
                  <select
                    value={selectedTask.status}
                    onChange={(e) => updateTaskStatus(selectedTask.task_id, e.target.value as any)}
                    className="px-3 py-2 border border-gray-300 rounded"
                  >
                    <option value="pending">Pending</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Created:</span>{' '}
                    {new Date(selectedTask.created_at).toLocaleString()}
                  </div>
                  {selectedTask.due_date && (
                    <div>
                      <span className="text-gray-500">Due Date:</span>{' '}
                      <span
                        className={
                          isOverdue(selectedTask.due_date) ? 'text-red-600 font-semibold' : ''
                        }
                      >
                        {new Date(selectedTask.due_date).toLocaleString()}
                      </span>
                    </div>
                  )}
                  {selectedTask.assignee && (
                    <div>
                      <span className="text-gray-500">Assignee:</span> {selectedTask.assignee}
                    </div>
                  )}
                  {selectedTask.category && (
                    <div>
                      <span className="text-gray-500">Category:</span> {selectedTask.category}
                    </div>
                  )}
                </div>

                {selectedTask.tags.length > 0 && (
                  <div className="mt-4">
                    <span className="text-gray-500 text-sm">Tags:</span>
                    <div className="flex gap-2 mt-1">
                      {selectedTask.tags.map((tag) => (
                        <span
                          key={tag}
                          className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Description */}
              <div className="mb-6 bg-white rounded-lg shadow p-4">
                <h4 className="font-semibold mb-3">Description</h4>
                <p className="text-gray-700 whitespace-pre-wrap">{selectedTask.description}</p>
              </div>

              {/* Related Email */}
              {selectedTask.email_id && (
                <div className="bg-white rounded-lg shadow p-4">
                  <h4 className="font-semibold mb-3">Related Email</h4>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">Email ID:</span>
                    <code className="text-sm bg-gray-100 px-2 py-1 rounded font-mono">
                      {selectedTask.email_id}
                    </code>
                    <button className="ml-auto px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600">
                      View Email
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              Select a task to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
