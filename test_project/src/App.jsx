import React, { useState, useEffect } from 'react'
import LoginForm from './components/LoginForm'
import TaskManager from './components/TaskManager'
import './App.css'

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in on app start
    const savedUser = localStorage.getItem('tresto-user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    }
    setLoading(false)
  }, [])

  const handleLogin = (userData) => {
    setUser(userData)
    localStorage.setItem('tresto-user', JSON.stringify(userData))
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('tresto-user')
    localStorage.removeItem('tresto-tasks')
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" data-testid="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <div className="app">
      {user ? (
        <TaskManager user={user} onLogout={handleLogout} />
      ) : (
        <LoginForm onLogin={handleLogin} />
      )}
    </div>
  )
}

export default App
