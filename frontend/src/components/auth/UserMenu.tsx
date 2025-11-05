/**
 * User Menu Component - Shows in header/navbar
 * Fast Track Phase 7 - Week 9 Day 6-7
 */

import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export function UserMenu() {
  const { user, isAuthenticated, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const handleLogout = () => {
    logout();
    setIsOpen(false);
    navigate('/login');
  };

  if (!isAuthenticated || !user) {
    // Not logged in - show login/register buttons
    return (
      <div className="flex items-center gap-2">
        <Link
          to="/login"
          className="px-4 py-2 text-sm border border-border rounded-md hover:bg-muted transition-colors"
        >
          Login
        </Link>
        <Link
          to="/register"
          className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          Sign Up
        </Link>
      </div>
    );
  }

  // Logged in - show user menu
  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted transition-colors"
      >
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-medium">
          {user.username.charAt(0).toUpperCase()}
        </div>
        <span className="text-sm font-medium hidden sm:inline">{user.username}</span>
        {user.is_admin && (
          <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded hidden sm:inline">
            Admin
          </span>
        )}
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-card border border-border z-50">
          <div className="py-1">
            {/* User Info */}
            <div className="px-4 py-3 border-b border-border">
              <p className="text-sm font-medium">{user.username}</p>
              <p className="text-xs text-muted-foreground truncate">{user.email}</p>
            </div>

            {/* Menu Items */}
            <Link
              to="/profile"
              onClick={() => setIsOpen(false)}
              className="block px-4 py-2 text-sm hover:bg-muted transition-colors"
            >
              👤 Profile
            </Link>

            <Link
              to="/settings"
              onClick={() => setIsOpen(false)}
              className="block px-4 py-2 text-sm hover:bg-muted transition-colors"
            >
              ⚙️ Settings
            </Link>

            {user.is_admin && (
              <Link
                to="/metrics"
                onClick={() => setIsOpen(false)}
                className="block px-4 py-2 text-sm hover:bg-muted transition-colors"
              >
                📊 Metrics
              </Link>
            )}

            <div className="border-t border-border my-1"></div>

            {/* Rate Limit Info */}
            <div className="px-4 py-2 text-xs text-muted-foreground">
              Rate Limit: {user.is_admin ? '1,000' : '100'} req/min
            </div>

            <div className="border-t border-border my-1"></div>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="block w-full text-left px-4 py-2 text-sm text-destructive hover:bg-muted transition-colors"
            >
              🚪 Logout
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

