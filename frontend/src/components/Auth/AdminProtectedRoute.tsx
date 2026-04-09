/**
 * Guards admin routes — redirects to /admin/login if not authenticated as admin.
 */

import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export default function AdminProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        height: '100vh',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#0a0a0f',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            background: '#6366f1',
            animation: 'pulse 1.2s ease-in-out infinite',
          }} />
          <span style={{ color: '#6b7280', fontFamily: 'monospace', fontSize: '0.75rem', letterSpacing: '0.1em' }}>
            AUTHENTICATING
          </span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  }

  if (user.role !== 'admin') {
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
