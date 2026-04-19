import React, { useState, useEffect } from 'react';
import { Menu, X, LogOut, User, ShieldAlert, ShieldCheck, BarChart3, LayoutDashboard, Bell } from 'lucide-react';
import './Navbar.css';

export default function Navbar({ username, isAuthenticated, isStaff, logoUrl, urls, csrfToken }) {
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);

  // Fetch notifications for authenticated users
  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchNotifications = async () => {
      try {
        const response = await fetch('/notifications/api/latest/');
        const data = await response.json();
        setUnreadCount(data.unread_count);
        setNotifications(data.notifications || []);
      } catch (error) {
        console.error("Error fetching notifications:", error);
      }
    };

    fetchNotifications();
    const interval = setInterval(fetchNotifications, 60000); // Poll every 60 seconds
    return () => clearInterval(interval);
  }, [isAuthenticated]);

  // Handle click outside to close notifications
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (showNotifications && !e.target.closest('.notif-wrapper') && !e.target.closest('.notif-dropdown')) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showNotifications]);

  const handleMarkAsRead = async () => {
    try {
      await fetch('/notifications/api/mark-read/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken }
      });
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (error) {
      console.error("Error marking read:", error);
    }
  };

  const renderNotifDropdown = () => {
    if (!showNotifications) return null;
    return (
      <div className="notif-dropdown">
        <div className="notif-header">Notifications</div>
        <div className="notif-body">
          {notifications.length > 0 ? (
            notifications.map(n => (
              <a key={n.id} href={n.url} className={`notif-item ${!n.is_read ? 'unread' : ''}`}>
                <div className="notif-msg">{n.message}</div>
                <div className="notif-time">{n.created_at}</div>
              </a>
            ))
          ) : (
            <div className="notif-empty">No notifications</div>
          )}
        </div>
      </div>
    );
  };

  return (
    <nav className="react-site-nav">
      {/* Brand Section */}
      <a href={urls.home} className="nav-brand-link">
        {logoUrl && <img src={logoUrl} alt="BanglaCERT Logo" className="nav-logo" />}
        <span className="nav-brand-text">BanglaCERT</span>
      </a>

      {/* Shared Notification Bell (shown on both mobile & desktop) */}
      {isAuthenticated && (
        <div className="notif-wrapper">
          <button 
            className={`notif-btn ${unreadCount > 0 ? 'pulse' : ''}`} 
            onClick={(e) => {
              e.stopPropagation();
              console.log("Notification Bell Clicked. Shared state:", showNotifications);
              setShowNotifications(!showNotifications);
              if (!showNotifications && unreadCount > 0) handleMarkAsRead();
            }}
          >
            <Bell size={20} color={unreadCount > 0 ? "#5B7BFF" : "currentColor"} />
            {unreadCount > 0 && <span className="notif-badge">{unreadCount}</span>}
          </button>
          {renderNotifDropdown()}
        </div>
      )}

      {/* Hamburger Menu Toggle for Mobile */}
      <div className="nav-actions-mobile">
        <button 
          className="mobile-menu-btn" 
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Toggle Navigation"
        >
          {isOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Navigation Links */}
      <div className={`nav-links-container ${isOpen ? 'open' : ''}`}>
        <div className="nav-primary">
          {isAuthenticated && isStaff ? (
            <>
              <a href={urls.admin} className="nav-link">
                <LayoutDashboard size={18} />
                Dashboard
              </a>
              <a href={urls.awareness} className="nav-link">
                <ShieldCheck size={18} />
                Verified Posts
              </a>
            </>
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
