import React, { useState } from 'react';
import { Menu, X, LogOut, User, ShieldAlert, BarChart3, LayoutDashboard } from 'lucide-react';
import './Navbar.css'; // Importing modular CSS for Navbar

export default function Navbar({ username, isAuthenticated, isStaff, logoUrl, urls, csrfToken }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="react-site-nav">
      {/* Brand Section */}
      <a href={urls.home} className="nav-brand-link">
        {logoUrl && <img src={logoUrl} alt="BanglaCERT Logo" className="nav-logo" />}
        <span className="nav-brand-text">BanglaCERT</span>
      </a>

      {/* Hamburger Menu Toggle for Mobile */}
      <button 
        className="mobile-menu-btn" 
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle Navigation"
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Navigation Links */}
      <div className={`nav-links-container ${isOpen ? 'open' : ''}`}>
        
        {/* Primary Links */}
        <div className="nav-primary">
          {isAuthenticated && isStaff ? (
            <a href={urls.admin} className="nav-link">
              <LayoutDashboard size={18} />
              Dashboard
            </a>
          ) : (
            <a href={urls.home} className="nav-link">
              <BarChart3 size={18} />
              Platform
            </a>
          )}
          
          {!isAuthenticated && (
            <a href={urls.report} className="nav-link highlight">
              <ShieldAlert size={18} />
              Report Incident
            </a>
          )}
          
          {isAuthenticated && !isStaff && (
            <a href={urls.myReports} className="nav-link">
              <ShieldAlert size={18} />
              My Reports
            </a>
          )}
        </div>

        {/* Auth Section */}
        <div className="nav-auth">
          {isAuthenticated ? (
            <div className="nav-user-menu">
              <span className="user-greeting">
                <User size={16} /> <strong>{username}</strong>
              </span>
              <form method="post" action={urls.logout} className="logout-form">
                <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
                <button type="submit" className="logout-btn">
                  <LogOut size={16} /> Logout
                </button>
              </form>
            </div>
          ) : (
            <>
              <a href={urls.login} className="nav-link">Login</a>
              <span className="auth-separator">|</span>
              <a href={urls.register} className="nav-link">Register</a>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
