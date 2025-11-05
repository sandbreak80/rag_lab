/**
 * User Profile Component
 * Fast Track Phase 7 - Week 9 Day 6-7
 */

import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export function UserProfile() {
  const { user, logout, changePassword } = useAuth();
  const navigate = useNavigate();

  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    try {
      await changePassword(oldPassword, newPassword);
      setSuccess('Password changed successfully!');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setIsChangingPassword(false);
    } catch (err: any) {
      setError(err.message || 'Password change failed');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted p-4">
      <div className="max-w-2xl mx-auto py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">👤 Profile</h1>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 text-sm border border-border rounded-md hover:bg-muted"
          >
            ← Back to Chat
          </button>
        </div>

        {/* User Info Card */}
        <div className="bg-card rounded-lg shadow-xl p-6 border border-border mb-6">
          <h2 className="text-xl font-semibold mb-4">Account Information</h2>

          <div className="space-y-4">
            <div>
              <label className="text-sm text-muted-foreground">Username</label>
              <p className="text-lg font-medium">{user.username}</p>
            </div>

            <div>
              <label className="text-sm text-muted-foreground">Email</label>
              <p className="text-lg">{user.email}</p>
            </div>

            <div>
              <label className="text-sm text-muted-foreground">Account Type</label>
              <p className="text-lg">
                {user.is_admin ? (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary/10 text-primary">
                    👑 Administrator
                  </span>
                ) : (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-muted text-foreground">
                    👤 User
                  </span>
                )}
              </p>
            </div>

            <div>
              <label className="text-sm text-muted-foreground">Member Since</label>
              <p className="text-lg">
                {new Date(user.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </p>
            </div>

            {user.last_login && (
              <div>
                <label className="text-sm text-muted-foreground">Last Login</label>
                <p className="text-lg">
                  {new Date(user.last_login).toLocaleString()}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Rate Limit Info */}
        <div className="bg-card rounded-lg shadow-xl p-6 border border-border mb-6">
          <h2 className="text-xl font-semibold mb-4">🔒 Access Limits</h2>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-md">
              <span className="text-sm font-medium">Rate Limit</span>
              <span className="text-sm text-primary font-bold">
                {user.is_admin ? '1,000' : '100'} requests/minute
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-md">
              <span className="text-sm font-medium">Security Features</span>
              <span className="text-sm text-green-600 font-bold">✅ All Enabled</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-md">
              <span className="text-sm font-medium">Session Duration</span>
              <span className="text-sm">1 hour (auto-refresh)</span>
            </div>
          </div>
        </div>

        {/* Password Change */}
        <div className="bg-card rounded-lg shadow-xl p-6 border border-border mb-6">
          <h2 className="text-xl font-semibold mb-4">🔑 Security</h2>

          {!isChangingPassword ? (
            <button
              onClick={() => setIsChangingPassword(true)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Change Password
            </button>
          ) : (
            <form onSubmit={handlePasswordChange} className="space-y-4">
              {error && (
                <div className="p-3 bg-destructive/10 border border-destructive rounded-md text-sm text-destructive">
                  {error}
                </div>
              )}

              {success && (
                <div className="p-3 bg-green-500/10 border border-green-500 rounded-md text-sm text-green-600">
                  {success}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium mb-2">Current Password</label>
                <input
                  type="password"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  required
                  className="w-full px-4 py-2 rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">New Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                  className="w-full px-4 py-2 rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Confirm New Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={8}
                  className="w-full px-4 py-2 rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                >
                  Update Password
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsChangingPassword(false);
                    setError('');
                    setSuccess('');
                  }}
                  className="px-4 py-2 border border-border rounded-md hover:bg-muted"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Logout */}
        <div className="bg-card rounded-lg shadow-xl p-6 border border-border">
          <h2 className="text-xl font-semibold mb-4">🚪 Sign Out</h2>
          <p className="text-sm text-muted-foreground mb-4">
            This will end your current session and log you out.
          </p>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}

