import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { SnackbarProvider } from 'notistack';
import { ErrorBoundary } from './components/ErrorBoundary/ErrorBoundary';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Backtester from './pages/Backtester';
import Results from './pages/Results';
import Comparison from './pages/Comparison';
import CosmicBackground from './components/CosmicBackground';

function App() {
  return (
    <ThemeProvider>
      <ErrorBoundary>
        <SnackbarProvider maxSnack={3}>
          <Router>
            <div className="min-h-screen bg-space-blue text-white relative">
              <CosmicBackground />
              <Navbar />
              <div className="container mx-auto px-4 py-8 relative z-10">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/backtester" element={<Backtester />} />
                  <Route path="/results" element={<Results />} />
                  <Route path="/comparison" element={<Comparison />} />
                </Routes>
              </div>
            </div>
          </Router>
        </SnackbarProvider>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

export default App;