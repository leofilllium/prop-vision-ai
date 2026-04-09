/**
 * Redirects unauthenticated users to /login.
 */

import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        height: '100vh',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg)',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.625rem',
        }}>
          <div style={{
            width: 20,
            height: 20,
            background: 'var(--accent)',
            borderRadius: 'var(--r-sm)',
            animation: 'pulse 1.4s var(--ease-in-out) infinite',
          }} />
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.6875rem',
            fontWeight: 700,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
          }}>
            Loading
          </span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
