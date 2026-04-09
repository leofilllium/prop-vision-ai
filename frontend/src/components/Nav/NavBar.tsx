/**
 * NavBar — minimal, asymmetric top-left positioning.
 * Logo + wordmark left-aligned, no centered row of links.
 */

import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './NavBar.css';

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <nav className="nav" id="main-nav">
      <Link to="/" className="nav-brand">
        <div className="nav-mark" aria-hidden="true" />
        <div className="nav-text">
          <span className="nav-name">PropVision</span>
          <span className="nav-tag">.AI</span>
        </div>
      </Link>
      <div className="nav-meta">
        <span className="label">Tashkent</span>
        <span className="nav-separator">/</span>
        <Link to="/analytics" className="nav-link label">Intelligence</Link>
        {user?.role === 'admin' && (
          <>
            <span className="nav-separator">/</span>
            <Link to="/admin" className="nav-link label">Admin</Link>
          </>
        )}
        {user && (
          <>
            <span className="nav-separator">/</span>
            <button onClick={handleLogout} className="nav-link label" style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              Sign out
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
