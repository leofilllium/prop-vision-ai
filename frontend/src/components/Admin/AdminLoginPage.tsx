/**
 * Admin-only login page — isolated from public login.
 */

import { useState, type FormEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './AdminLoginPage.css';

export default function AdminLoginPage() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/admin';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Already logged in as admin
  if (user?.role === 'admin') {
    navigate('/admin', { replace: true });
    return null;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      await login(email, password);
      // login sets user — check role after
      // We navigate and AdminProtectedRoute will block non-admins
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      const msg =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((e: { msg?: string }) => e.msg ?? 'Validation error').join('. ')
            : 'Invalid credentials.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="al-root">
      <div className="al-grid-bg" aria-hidden="true" />

      <div className="al-card">
        {/* Badge */}
        <div className="al-badge">
          <span className="al-badge-dot" />
          ADMIN ACCESS
        </div>

        {/* Logo */}
        <div className="al-logo">
          <div className="al-logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
              <path d="M2 17l10 5 10-5" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
              <path d="M2 12l10 5 10-5" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <div className="al-logo-name">PropVision<span className="al-logo-ai">.AI</span></div>
            <div className="al-logo-sub">Control Panel</div>
          </div>
        </div>

        <h1 className="al-heading">Admin Sign In</h1>
        <p className="al-desc">Restricted access. Admin credentials required.</p>

        <form onSubmit={handleSubmit} className="al-form" noValidate>
          <div className="al-field">
            <label className="al-label" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="al-input"
              placeholder="admin@example.com"
              autoComplete="email"
              autoFocus
            />
          </div>

          <div className="al-field">
            <label className="al-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="al-input"
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </div>

          {error && (
            <div className="al-error" role="alert">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5"/>
                <path d="M12 8v4m0 4h.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
              {error}
            </div>
          )}

          <button type="submit" disabled={isSubmitting} className="al-submit">
            {isSubmitting ? (
              <span className="al-spinner-row">
                <span className="al-spinner" />
                Authenticating…
              </span>
            ) : (
              'Sign In to Admin Panel →'
            )}
          </button>
        </form>

        <div className="al-footer">
          <a href="/" className="al-back">← Back to app</a>
          <span className="al-version">v1.0</span>
        </div>
      </div>
    </div>
  );
}
