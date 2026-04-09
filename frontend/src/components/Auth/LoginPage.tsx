/**
 * Login page — matches PropVision.AI design system.
 */

import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './LoginPage.css';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      const msg =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((e: { msg?: string }) => e.msg ?? 'Validation error').join('. ')
            : 'Invalid email or password.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="login-root grain">
      <div className="login-shell">

        {/* Wordmark */}
        <div className="login-brand">
          <div className="login-mark" aria-hidden="true" />
          <div className="login-wordmark">
            <span className="login-name">PropVision</span>
            <span className="login-dot-ai">.AI</span>
          </div>
        </div>

        <h1 className="login-heading">Sign in</h1>
        <p className="login-sub">
          No account?{' '}
          <Link to="/register" className="login-switch-link">Create one →</Link>
        </p>

        <form onSubmit={handleSubmit} className="login-form" noValidate>
          <div className="login-field">
            <label className="login-label" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              placeholder="you@example.com"
              autoComplete="email"
              autoFocus
            />
          </div>

          <div className="login-field">
            <label className="login-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </div>

          {error && (
            <p className="login-error" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="btn btn-primary login-submit"
          >
            {isSubmitting ? 'Signing in…' : 'Sign in →'}
          </button>
        </form>

        <p className="login-footer">Prop Vision — Tashkent, UZ</p>
      </div>
    </div>
  );
}
