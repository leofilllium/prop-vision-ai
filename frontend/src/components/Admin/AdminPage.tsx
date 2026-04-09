/**
 * Admin control panel — user management + rich system analytics.
 */

import { useState } from 'react';
import { useAdminStats, useAllUsers, useUpdateUser, useDeleteUser } from '../../hooks/useApi';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import type { UserInfo } from '../../api/client';
import './AdminPage.css';

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(n: number) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return n.toString();
}

function fmtPrice(n: number) {
  if (n >= 1_000_000) return '$' + (n / 1_000_000).toFixed(2) + 'M';
  if (n >= 1_000) return '$' + (n / 1_000).toFixed(0) + 'K';
  return '$' + n.toFixed(0);
}

function timeAgo(iso?: string) {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function roleBadgeClass(role: string) {
  if (role === 'admin') return 'role-admin';
  if (role === 'analyst') return 'role-analyst';
  return 'role-viewer';
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function AdminPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const isAdmin = user?.role === 'admin';
  const { data: stats, isLoading: statsLoading, error: statsError } = useAdminStats(isAdmin);
  const { data: users, isLoading: usersLoading, refetch: refetchUsers } = useAllUsers(isAdmin);

  const updateUserMutation = useUpdateUser();
  const deleteUserMutation = useDeleteUser();

  const [selectedUser, setSelectedUser] = useState<UserInfo | null>(null);
  const [editingRole, setEditingRole] = useState('');
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'properties'>('overview');
  const [searchQuery, setSearchQuery] = useState('');

  const handleUpdateRole = async (userId: string, newRole: string) => {
    try {
      await updateUserMutation.mutateAsync({ userId, updates: { role: newRole } });
      refetchUsers();
      setSelectedUser(null);
    } catch (err) {
      console.error('Failed to update user:', err);
    }
  };

  const handleToggleActive = async (userId: string, currentActive: boolean) => {
    try {
      await updateUserMutation.mutateAsync({ userId, updates: { is_active: !currentActive } });
      refetchUsers();
    } catch (err) {
      console.error('Failed to toggle user:', err);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Permanently delete this user?')) return;
    try {
      await deleteUserMutation.mutateAsync(userId);
      refetchUsers();
      setSelectedUser(null);
    } catch (err) {
      console.error('Failed to delete user:', err);
    }
  };

  const filteredUsers = users?.filter((u) =>
    u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.role.toLowerCase().includes(searchQuery.toLowerCase())
  ) ?? [];

  // Percentage helpers
  const pct = (n: number, total: number) =>
    total > 0 ? Math.round((n / total) * 100) : 0;

  return (
    <div className="ap-root">
      {/* Sidebar */}
      <aside className="ap-sidebar">
        <div className="ap-sidebar-logo">
          <div className="ap-sidebar-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
              <path d="M2 17l10 5 10-5" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
              <path d="M2 12l10 5 10-5" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <div className="ap-sidebar-name">PropVision<span>.AI</span></div>
            <div className="ap-sidebar-sub">Admin Panel</div>
          </div>
        </div>

        <nav className="ap-nav">
          <button
            className={`ap-nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5"/>
              <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5"/>
              <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5"/>
              <rect x="14" y="14" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5"/>
            </svg>
            Overview
          </button>
          <button
            className={`ap-nav-item ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              <circle cx="9" cy="7" r="4" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            Users
            {users && <span className="ap-nav-badge">{users.length}</span>}
          </button>
          <button
            className={`ap-nav-item ${activeTab === 'properties' ? 'active' : ''}`}
            onClick={() => setActiveTab('properties')}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
              <path d="M9 22V12h6v10" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
            </svg>
            Properties
          </button>
        </nav>

        <div className="ap-sidebar-bottom">
          <div className="ap-user-card">
            <div className="ap-user-avatar">{user?.email[0].toUpperCase()}</div>
            <div className="ap-user-info">
              <div className="ap-user-email">{user?.email}</div>
              <div className="ap-user-role">Administrator</div>
            </div>
          </div>
          <div className="ap-sidebar-actions">
            <button className="ap-action-btn" onClick={() => navigate('/')} title="Go to app">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" strokeWidth="1.5"/>
              </svg>
            </button>
            <button className="ap-action-btn ap-action-danger" onClick={logout} title="Sign out">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                <path d="M16 17l5-5-5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M21 12H9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="ap-main">
        {/* Top bar */}
        <div className="ap-topbar">
          <div>
            <h1 className="ap-page-title">
              {activeTab === 'overview' && 'System Overview'}
              {activeTab === 'users' && 'User Management'}
              {activeTab === 'properties' && 'Property Analytics'}
            </h1>
            <p className="ap-page-sub">
              {activeTab === 'overview' && 'Real-time platform statistics and health'}
              {activeTab === 'users' && 'Manage accounts, roles, and access'}
              {activeTab === 'properties' && 'Listing inventory and engagement'}
            </p>
          </div>
          <div className="ap-topbar-right">
            <div className="ap-live-dot" title="Live data" />
            <span className="ap-live-label">Live</span>
          </div>
        </div>

        {/* ── OVERVIEW TAB ─────────────────────────────────────────────── */}
        {activeTab === 'overview' && (
          <div className="ap-overview">
            {statsLoading ? (
              <div className="ap-skeleton-grid">
                {[...Array(8)].map((_, i) => <div key={i} className="ap-skeleton ap-skeleton-card" />)}
              </div>
            ) : statsError ? (
              <div className="ap-error-state">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5"/>
                  <path d="M12 8v4m0 4h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
                Failed to load stats. Check API connectivity.
              </div>
            ) : stats ? (
              <>
                {/* ── KPI strip */}
                <div className="ap-kpi-grid">
                  <div className="ap-kpi">
                    <div className="ap-kpi-label">Total Users</div>
                    <div className="ap-kpi-value">{fmt(stats.total_users)}</div>
                    <div className="ap-kpi-delta ap-kpi-green">+{stats.new_users_today} today</div>
                  </div>
                  <div className="ap-kpi">
                    <div className="ap-kpi-label">Active Users</div>
                    <div className="ap-kpi-value">{fmt(stats.active_users)}</div>
                    <div className="ap-kpi-delta">{pct(stats.active_users, stats.total_users)}% of total</div>
                  </div>
                  <div className="ap-kpi">
                    <div className="ap-kpi-label">Properties</div>
                    <div className="ap-kpi-value">{fmt(stats.total_properties)}</div>
                    <div className="ap-kpi-delta">{fmt(stats.active_properties)} active</div>
                  </div>
                  <div className="ap-kpi">
                    <div className="ap-kpi-label">Avg. Price</div>
                    <div className="ap-kpi-value">{fmtPrice(stats.avg_price)}</div>
                    <div className="ap-kpi-delta">across all listings</div>
                  </div>
                  <div className="ap-kpi">
                    <div className="ap-kpi-label">New This Week</div>
                    <div className="ap-kpi-value">{stats.new_users_week}</div>
                    <div className="ap-kpi-delta">user signups</div>
                  </div>
                  <div className="ap-kpi">
                    <div className="ap-kpi-label">3D Models</div>
                    <div className="ap-kpi-value">{fmt(stats.properties_with_3d)}</div>
                    <div className="ap-kpi-delta">{pct(stats.properties_with_3d, stats.total_properties)}% coverage</div>
                  </div>
                  <div className="ap-kpi">
                    <div className="ap-kpi-label">Video Walkthroughs</div>
                    <div className="ap-kpi-value">{fmt(stats.properties_with_video)}</div>
                    <div className="ap-kpi-delta">{pct(stats.properties_with_video, stats.total_properties)}% coverage</div>
                  </div>
                  <div className="ap-kpi">
                    <div className="ap-kpi-label">Partners</div>
                    <div className="ap-kpi-value">{stats.total_partners}</div>
                    <div className="ap-kpi-delta">{stats.active_partners} active</div>
                  </div>
                </div>

                {/* ── Two-column detail */}
                <div className="ap-detail-grid">
                  {/* User role breakdown */}
                  <div className="ap-card">
                    <div className="ap-card-header">
                      <h3 className="ap-card-title">User Roles</h3>
                    </div>
                    <div className="ap-role-list">
                      <div className="ap-role-row">
                        <div className="ap-role-info">
                          <span className="ap-role-dot ap-dot-admin" />
                          <span className="ap-role-name">Admin</span>
                        </div>
                        <div className="ap-role-right">
                          <div className="ap-role-bar-wrap">
                            <div className="ap-role-bar" style={{ width: `${pct(stats.admin_users, stats.total_users)}%`, background: '#6366f1' }} />
                          </div>
                          <span className="ap-role-count">{stats.admin_users}</span>
                        </div>
                      </div>
                      <div className="ap-role-row">
                        <div className="ap-role-info">
                          <span className="ap-role-dot ap-dot-analyst" />
                          <span className="ap-role-name">Analyst</span>
                        </div>
                        <div className="ap-role-right">
                          <div className="ap-role-bar-wrap">
                            <div className="ap-role-bar" style={{ width: `${pct(stats.analyst_users, stats.total_users)}%`, background: '#f59e0b' }} />
                          </div>
                          <span className="ap-role-count">{stats.analyst_users}</span>
                        </div>
                      </div>
                      <div className="ap-role-row">
                        <div className="ap-role-info">
                          <span className="ap-role-dot ap-dot-viewer" />
                          <span className="ap-role-name">Viewer</span>
                        </div>
                        <div className="ap-role-right">
                          <div className="ap-role-bar-wrap">
                            <div className="ap-role-bar" style={{ width: `${pct(stats.viewer_users, stats.total_users)}%`, background: '#10b981' }} />
                          </div>
                          <span className="ap-role-count">{stats.viewer_users}</span>
                        </div>
                      </div>
                      <div className="ap-role-row">
                        <div className="ap-role-info">
                          <span className="ap-role-dot ap-dot-inactive" />
                          <span className="ap-role-name">Inactive</span>
                        </div>
                        <div className="ap-role-right">
                          <div className="ap-role-bar-wrap">
                            <div className="ap-role-bar" style={{ width: `${pct(stats.inactive_users, stats.total_users)}%`, background: '#6b7280' }} />
                          </div>
                          <span className="ap-role-count">{stats.inactive_users}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Districts */}
                  <div className="ap-card">
                    <div className="ap-card-header">
                      <h3 className="ap-card-title">Top Districts by Listings</h3>
                    </div>
                    {stats.districts.length === 0 ? (
                      <p className="ap-empty-text">No district data available</p>
                    ) : (
                      <div className="ap-district-list">
                        {stats.districts.map((d, i) => (
                          <div key={d.district} className="ap-district-row">
                            <span className="ap-district-rank">#{i + 1}</span>
                            <span className="ap-district-name">{d.district}</span>
                            <div className="ap-district-bar-wrap">
                              <div
                                className="ap-district-bar"
                                style={{ width: `${pct(d.count, stats.districts[0].count)}%` }}
                              />
                            </div>
                            <span className="ap-district-count">{fmt(d.count)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Recent signups */}
                  <div className="ap-card ap-card-wide">
                    <div className="ap-card-header">
                      <h3 className="ap-card-title">Recent Signups</h3>
                      <button className="ap-card-link" onClick={() => setActiveTab('users')}>
                        View all →
                      </button>
                    </div>
                    <table className="ap-mini-table">
                      <thead>
                        <tr>
                          <th>Email</th>
                          <th>Role</th>
                          <th>Status</th>
                          <th>Joined</th>
                        </tr>
                      </thead>
                      <tbody>
                        {stats.recent_users.map((u) => (
                          <tr key={u.id}>
                            <td className="ap-email-cell">{u.email}</td>
                            <td><span className={`ap-role-badge ${roleBadgeClass(u.role)}`}>{u.role}</span></td>
                            <td>
                              <span className={`ap-status-dot ${u.is_active ? 'dot-active' : 'dot-inactive'}`} />
                              {u.is_active ? 'Active' : 'Inactive'}
                            </td>
                            <td className="ap-muted">{timeAgo(u.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Property health */}
                  <div className="ap-card">
                    <div className="ap-card-header">
                      <h3 className="ap-card-title">Listing Health</h3>
                    </div>
                    <div className="ap-health-grid">
                      <div className="ap-health-item">
                        <div className="ap-health-ring" style={{ '--pct': `${pct(stats.active_properties, stats.total_properties)}` } as React.CSSProperties}>
                          <span>{pct(stats.active_properties, stats.total_properties)}%</span>
                        </div>
                        <div className="ap-health-label">Active</div>
                      </div>
                      <div className="ap-health-item">
                        <div className="ap-health-ring ap-ring-purple" style={{ '--pct': `${pct(stats.properties_with_3d, stats.total_properties)}` } as React.CSSProperties}>
                          <span>{pct(stats.properties_with_3d, stats.total_properties)}%</span>
                        </div>
                        <div className="ap-health-label">3D Ready</div>
                      </div>
                      <div className="ap-health-item">
                        <div className="ap-health-ring ap-ring-amber" style={{ '--pct': `${pct(stats.properties_with_video, stats.total_properties)}` } as React.CSSProperties}>
                          <span>{pct(stats.properties_with_video, stats.total_properties)}%</span>
                        </div>
                        <div className="ap-health-label">Video</div>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : null}
          </div>
        )}

        {/* ── USERS TAB ────────────────────────────────────────────────── */}
        {activeTab === 'users' && (
          <div className="ap-users-section">
            {/* Search + count */}
            <div className="ap-users-toolbar">
              <div className="ap-search-wrap">
                <svg className="ap-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="1.5"/>
                  <path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
                <input
                  type="text"
                  className="ap-search"
                  placeholder="Search by email or role…"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <span className="ap-users-count">{filteredUsers.length} users</span>
            </div>

            {usersLoading ? (
              <div className="ap-skeleton-list">
                {[...Array(5)].map((_, i) => <div key={i} className="ap-skeleton ap-skeleton-row" />)}
              </div>
            ) : filteredUsers.length === 0 ? (
              <div className="ap-empty-state">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  <circle cx="9" cy="7" r="4" stroke="currentColor" strokeWidth="1.5"/>
                </svg>
                <p>No users found</p>
              </div>
            ) : (
              <div className="ap-table-wrap">
                <table className="ap-table">
                  <thead>
                    <tr>
                      <th>User</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th>Joined</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUsers.map((u) => (
                      <tr key={u.id} className={selectedUser?.id === u.id ? 'ap-row-selected' : ''}>
                        <td>
                          <div className="ap-user-row">
                            <div className="ap-avatar">{u.email[0].toUpperCase()}</div>
                            <span className="ap-email">{u.email}</span>
                            {u.id === user?.id && <span className="ap-you-tag">You</span>}
                          </div>
                        </td>
                        <td>
                          <span className={`ap-role-badge ${roleBadgeClass(u.role)}`}>{u.role}</span>
                        </td>
                        <td>
                          <button
                            className={`ap-toggle ${u.is_active ? 'toggle-on' : 'toggle-off'}`}
                            onClick={() => handleToggleActive(u.id, u.is_active)}
                            disabled={u.id === user?.id}
                            title={u.is_active ? 'Click to deactivate' : 'Click to activate'}
                          >
                            <span className="ap-toggle-knob" />
                            {u.is_active ? 'Active' : 'Inactive'}
                          </button>
                        </td>
                        <td className="ap-muted">{timeAgo(u.created_at)}</td>
                        <td>
                          <div className="ap-row-actions">
                            <button
                              className="ap-btn ap-btn-sm ap-btn-ghost"
                              onClick={() => { setSelectedUser(u); setEditingRole(u.role); }}
                            >
                              Edit
                            </button>
                            {u.id !== user?.id && (
                              <button
                                className="ap-btn ap-btn-sm ap-btn-danger-ghost"
                                onClick={() => handleDeleteUser(u.id)}
                              >
                                Delete
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ── PROPERTIES TAB ───────────────────────────────────────────── */}
        {activeTab === 'properties' && (
          <div className="ap-overview">
            {statsLoading ? (
              <div className="ap-skeleton-grid">
                {[...Array(4)].map((_, i) => <div key={i} className="ap-skeleton ap-skeleton-card" />)}
              </div>
            ) : stats ? (
              <>
                <div className="ap-kpi-grid ap-kpi-grid-4">
                  <div className="ap-kpi">
                    <div className="ap-kpi-label">Total Listings</div>
                    <div className="ap-kpi-value">{fmt(stats.total_properties)}</div>
                    <div className="ap-kpi-delta">{fmt(stats.active_properties)} active</div>
                  </div>
                  <div className="ap-kpi">
                    <div className="ap-kpi-label">Average Price</div>
                    <div className="ap-kpi-value">{fmtPrice(stats.avg_price)}</div>
                    <div className="ap-kpi-delta">USD</div>
                  </div>
                  <div className="ap-kpi">
                    <div className="ap-kpi-label">3D Models</div>
                    <div className="ap-kpi-value">{fmt(stats.properties_with_3d)}</div>
                    <div className="ap-kpi-delta">{pct(stats.properties_with_3d, stats.total_properties)}% of listings</div>
                  </div>
                  <div className="ap-kpi">
                    <div className="ap-kpi-label">Video Tours</div>
                    <div className="ap-kpi-value">{fmt(stats.properties_with_video)}</div>
                    <div className="ap-kpi-delta">{pct(stats.properties_with_video, stats.total_properties)}% of listings</div>
                  </div>
                </div>

                <div className="ap-detail-grid">
                  <div className="ap-card ap-card-wide">
                    <div className="ap-card-header">
                      <h3 className="ap-card-title">Listings by District</h3>
                    </div>
                    {stats.districts.length === 0 ? (
                      <p className="ap-empty-text">No district data</p>
                    ) : (
                      <div className="ap-district-chart">
                        {stats.districts.map((d) => (
                          <div key={d.district} className="ap-district-bar-item">
                            <div
                              className="ap-district-bar-v"
                              style={{ height: `${pct(d.count, stats.districts[0].count) * 0.8 + 20}px` }}
                              title={`${d.district}: ${d.count}`}
                            />
                            <div className="ap-district-bar-label">{d.district.length > 10 ? d.district.slice(0, 10) + '…' : d.district}</div>
                            <div className="ap-district-bar-val">{fmt(d.count)}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="ap-card">
                    <div className="ap-card-header">
                      <h3 className="ap-card-title">Partners</h3>
                    </div>
                    <div className="ap-partner-stats">
                      <div className="ap-partner-row">
                        <span>Total partners</span>
                        <strong>{stats.total_partners}</strong>
                      </div>
                      <div className="ap-partner-row">
                        <span>Active partners</span>
                        <strong className="ap-green">{stats.active_partners}</strong>
                      </div>
                      <div className="ap-partner-row">
                        <span>Inactive partners</span>
                        <strong className="ap-red">{stats.total_partners - stats.active_partners}</strong>
                      </div>
                      <div className="ap-partner-row">
                        <span>Properties per partner</span>
                        <strong>{stats.active_partners > 0 ? Math.round(stats.total_properties / stats.active_partners) : '—'}</strong>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : null}
          </div>
        )}
      </main>

      {/* ── Edit User Modal ──────────────────────────────────────────────── */}
      {selectedUser && (
        <div className="ap-modal-overlay" onClick={() => setSelectedUser(null)}>
          <div className="ap-modal" onClick={(e) => e.stopPropagation()}>
            <div className="ap-modal-header">
              <div className="ap-modal-user">
                <div className="ap-avatar ap-avatar-lg">{selectedUser.email[0].toUpperCase()}</div>
                <div>
                  <div className="ap-modal-email">{selectedUser.email}</div>
                  <div className="ap-modal-meta">ID: {selectedUser.id.slice(0, 8)}…</div>
                </div>
              </div>
              <button className="ap-modal-close" onClick={() => setSelectedUser(null)}>✕</button>
            </div>

            <div className="ap-modal-body">
              <div className="ap-form-group">
                <label className="ap-form-label">Role</label>
                <select
                  value={editingRole}
                  onChange={(e) => setEditingRole(e.target.value)}
                  className="ap-select"
                  disabled={selectedUser.id === user?.id}
                >
                  <option value="viewer">Viewer — read-only access</option>
                  <option value="analyst">Analyst — analytics access</option>
                  <option value="admin">Admin — full access</option>
                </select>
                {selectedUser.id === user?.id && (
                  <p className="ap-form-hint">You cannot change your own role.</p>
                )}
              </div>

              <div className="ap-form-group">
                <label className="ap-form-label">Account Status</label>
                <div className="ap-status-options">
                  <label className="ap-radio-option">
                    <input
                      type="radio"
                      name="status"
                      checked={selectedUser.is_active}
                      onChange={() => handleToggleActive(selectedUser.id, !selectedUser.is_active)}
                      disabled={selectedUser.id === user?.id}
                    />
                    <span className="ap-radio-label">
                      <span className="ap-status-dot dot-active" />
                      Active
                    </span>
                  </label>
                  <label className="ap-radio-option">
                    <input
                      type="radio"
                      name="status"
                      checked={!selectedUser.is_active}
                      onChange={() => handleToggleActive(selectedUser.id, !selectedUser.is_active)}
                      disabled={selectedUser.id === user?.id}
                    />
                    <span className="ap-radio-label">
                      <span className="ap-status-dot dot-inactive" />
                      Inactive
                    </span>
                  </label>
                </div>
              </div>
            </div>

            <div className="ap-modal-footer">
              <button className="ap-btn ap-btn-ghost" onClick={() => setSelectedUser(null)}>
                Cancel
              </button>
              {selectedUser.id !== user?.id && (
                <button
                  className="ap-btn ap-btn-danger"
                  onClick={() => handleDeleteUser(selectedUser.id)}
                  disabled={deleteUserMutation.isPending}
                >
                  {deleteUserMutation.isPending ? 'Deleting…' : 'Delete User'}
                </button>
              )}
              <button
                className="ap-btn ap-btn-primary"
                onClick={() => handleUpdateRole(selectedUser.id, editingRole)}
                disabled={updateUserMutation.isPending || selectedUser.id === user?.id}
              >
                {updateUserMutation.isPending ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
