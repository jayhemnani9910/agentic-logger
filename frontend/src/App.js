import React, { useState } from 'react';
import './App.css';
import ActivityDashboard from './components/ActivityDashboard';

function App() {
  const [currentView, setCurrentView] = useState('activity');

  return (
    <div className="App">
      <nav className="app-navbar">
        <div className="navbar-brand">
          <h1>🚀 Agentic Logger</h1>
          <p className="navbar-subtitle">Personal Activity Intelligence System</p>
        </div>
        <div className="navbar-menu">
          <button 
            className={`nav-button ${currentView === 'activity' ? 'active' : ''}`}
            onClick={() => setCurrentView('activity')}
          >
            📊 Activity
          </button>
        </div>
      </nav>

      <main className="app-main">
        {currentView === 'activity' && <ActivityDashboard />}
      </main>

      <footer className="app-footer">
        <p>© 2025 Agentic Logger | Real-time Personal Activity Tracking</p>
      </footer>
    </div>
  );
}

export default App;
