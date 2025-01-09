import React from 'react';
import { Link } from 'react-router-dom';
import { BarChart2, GitCompare, Home, Settings, Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const Navbar: React.FC = () => {
  const { darkMode, toggleDarkMode } = useTheme();

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-md">
      <div className="container mx-auto px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Link to="/" className="text-xl font-bold text-gray-800 dark:text-white hover:text-gray-700 dark:hover:text-gray-300">
              <BarChart2 className="inline-block mr-2" />
              Backtesting App
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            <NavLink to="/" icon={<Home />} text="Dashboard" />
            <NavLink to="/backtester" icon={<Settings />} text="Backtester" />
            <NavLink to="/results" icon={<BarChart2 />} text="Results" />
            <NavLink to="/comparison" icon={<GitCompare />} text="Comparison" />
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white"
              aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
            >
              {darkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

const NavLink: React.FC<{ to: string; icon: React.ReactNode; text: string }> = ({ to, icon, text }) => (
  <Link to={to} className="flex items-center text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
    {icon}
    <span className="ml-2">{text}</span>
  </Link>
);

export default Navbar;