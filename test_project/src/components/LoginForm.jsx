import React, { useState } from 'react';
import './LoginForm.css';

const LoginForm = ({ onLogin }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      // Simple validation for demo purposes
      if (formData.username === 'admin' && formData.password === 'password') {
        onLogin(formData.username);
      } else if (formData.username.length >= 3 && formData.password.length >= 6) {
        onLogin(formData.username);
      } else {
        setErrors({
          general: 'Invalid username or password. Try "admin" / "password" or any username (3+ chars) with password (6+ chars)'
        });
      }
      setIsLoading(false);
    }, 1000);
  };

  return (
    <div className="login-container" data-testid="login-container">
      <h1 className="login-title" data-testid="login-title">
        Welcome to TaskMaster
      </h1>
      
      <form onSubmit={handleSubmit} data-testid="login-form">
        <div className="form-group">
          <label htmlFor="username" className="form-label">
            Username
          </label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            className={`form-input ${errors.username ? 'error' : ''}`}
            placeholder="Enter your username"
            data-testid="username-input"
            autoComplete="username"
          />
          {errors.username && (
            <div className="error-message" data-testid="username-error">
              {errors.username}
            </div>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="password" className="form-label">
            Password
          </label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            className={`form-input ${errors.password ? 'error' : ''}`}
            placeholder="Enter your password"
            data-testid="password-input"
            autoComplete="current-password"
          />
          {errors.password && (
            <div className="error-message" data-testid="password-error">
              {errors.password}
            </div>
          )}
        </div>

        {errors.general && (
          <div className="error-message" data-testid="general-error" style={{ marginBottom: '20px' }}>
            {errors.general}
          </div>
        )}

        <button
          type="submit"
          className="login-button"
          disabled={isLoading}
          data-testid="login-button"
        >
          {isLoading ? 'Signing In...' : 'Sign In'}
        </button>
      </form>

      <div style={{ marginTop: '20px', padding: '15px', background: '#f8f9fa', borderRadius: '6px', fontSize: '14px', color: '#666' }}>
        <strong>Demo Credentials:</strong><br />
        • Username: admin, Password: password<br />
        • Or any username (3+ chars) with password (6+ chars)
      </div>
    </div>
  );
};

export default LoginForm;
