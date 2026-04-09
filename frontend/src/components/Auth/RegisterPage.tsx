/**
 * Registration page — matches PropVision.AI design system.
 */

import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { apiRegister } from '../../api/client';
import './LoginPage.css';

export default function RegisterPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');

    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }

    setIsSubmitting(true);
    try {
      await apiRegister(email, password);
      await login(email, password);
      navigate('/', { replace: true });
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Registration failed. Please try again.';
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

        <h1 className="login-heading">Create account</h1>
        <p className="login-sub">
          Already have one?{' '}
          <Link to="/login" className="login-switch-link">Sign in →</Link>
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
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              placeholder="Min. 8 characters"
              autoComplete="new-password"
            />
          </div>

          <div className="login-field">
            <label className="login-label" htmlFor="confirm">Confirm password</label>
            <input
              id="confirm"
              type="password"
              required
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className="input"
              placeholder="••••••••"
              autoComplete="new-password"
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
            {isSubmitting ? 'Creating account…' : 'Create account →'}
          </button>
        </form>

        <p className="login-footer">Prop Vision — Tashkent, UZ</p>
      </div>
    </div>
  );
}
