import React, { useState, useEffect } from 'react';
import { Trash2, Plus, CheckCircle, Circle, BarChart3 } from 'lucide-react';
import './TaskManager.css';

const TaskManager = ({ user, onLogout }) => {
  const [tasks, setTasks] = useState([]);
  const [newTask, setNewTask] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Load tasks from localStorage on component mount
  useEffect(() => {
    const loadTasks = () => {
      try {
        const savedTasks = localStorage.getItem(`tasks_${user}`);
        if (savedTasks) {
          setTasks(JSON.parse(savedTasks));
        }
      } catch (error) {
        console.error('Error loading tasks:', error);
      } finally {
        setIsLoading(false);
      }
    };

    // Simulate loading delay for demo purposes
    setTimeout(loadTasks, 500);
  }, [user]);

  // Save tasks to localStorage whenever tasks change
  useEffect(() => {
    if (!isLoading) {
      try {
        localStorage.setItem(`tasks_${user}`, JSON.stringify(tasks));
      } catch (error) {
        console.error('Error saving tasks:', error);
      }
    }
  }, [tasks, user, isLoading]);

  const addTask = (e) => {
    e.preventDefault();
    
    if (!newTask.trim()) {
      return;
    }

    const task = {
      id: Date.now().toString(),
      text: newTask.trim(),
      completed: false,
      createdAt: new Date().toISOString()
    };

    setTasks(prev => [task, ...prev]);
    setNewTask('');
  };

  const toggleTask = (taskId) => {
    setTasks(prev =>
      prev.map(task =>
        task.id === taskId
          ? { ...task, completed: !task.completed }
          : task
      )
    );
  };

  const deleteTask = (taskId) => {
    setTasks(prev => prev.filter(task => task.id !== taskId));
  };

  const completedTasks = tasks.filter(task => task.completed).length;
  const pendingTasks = tasks.length - completedTasks;

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (isLoading) {
    return (
      <div className="loading-container" data-testid="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading your tasks...</p>
      </div>
    );
  }

  return (
    <div className="task-manager" data-testid="task-manager">
      <div className="task-header">
        <div className="welcome-text" data-testid="welcome-message">
          Welcome back, {user}!
        </div>
        <div className="user-info">
          <BarChart3 size={20} />
          <span data-testid="user-name">{user}</span>
          <button
            onClick={onLogout}
            className="logout-button"
            data-testid="logout-button"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="task-content">
        {/* Task Statistics */}
        <div className="task-stats" data-testid="task-stats">
          <div className="stat-item">
            <div className="stat-number" data-testid="total-tasks">
              {tasks.length}
            </div>
            <div className="stat-label">Total Tasks</div>
          </div>
          <div className="stat-item">
            <div className="stat-number" data-testid="pending-tasks">
              {pendingTasks}
            </div>
            <div className="stat-label">Pending</div>
          </div>
          <div className="stat-item">
            <div className="stat-number" data-testid="completed-tasks">
              {completedTasks}
            </div>
            <div className="stat-label">Completed</div>
          </div>
        </div>

        {/* Add New Task Form */}
        <form onSubmit={addTask} className="task-form" data-testid="add-task-form">
          <input
            type="text"
            value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
            placeholder="What needs to be done?"
            className="task-input"
            data-testid="new-task-input"
            maxLength={200}
          />
          <button
            type="submit"
            className="add-button"
            disabled={!newTask.trim()}
            data-testid="add-task-button"
          >
            <Plus size={16} style={{ marginRight: '5px' }} />
            Add Task
          </button>
        </form>

        {/* Task List */}
        <div data-testid="task-list-container">
          {tasks.length === 0 ? (
            <div className="empty-state" data-testid="empty-state">
              <Circle size={48} style={{ margin: '0 auto 20px', opacity: 0.3 }} />
              <p>No tasks yet. Add your first task above!</p>
            </div>
          ) : (
            <ul className="task-list" data-testid="task-list">
              {tasks.map((task) => (
                <li
                  key={task.id}
                  className={`task-item ${task.completed ? 'completed' : ''}`}
                  data-testid={`task-item-${task.id}`}
                >
                  <input
                    type="checkbox"
                    checked={task.completed}
                    onChange={() => toggleTask(task.id)}
                    className="task-checkbox"
                    data-testid={`task-checkbox-${task.id}`}
                  />
                  
                  <div className="task-content-wrapper" style={{ flex: 1 }}>
                    <span
                      className={`task-text ${task.completed ? 'completed' : ''}`}
                      data-testid={`task-text-${task.id}`}
                    >
                      {task.text}
                    </span>
                    <div className="task-date" data-testid={`task-date-${task.id}`}>
                      {formatDate(task.createdAt)}
                    </div>
                  </div>

                  <button
                    onClick={() => deleteTask(task.id)}
                    className="delete-button"
                    data-testid={`delete-task-${task.id}`}
                    title="Delete task"
                  >
                    <Trash2 size={14} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default TaskManager;
