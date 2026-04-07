import React from 'react';
import { createRoot } from 'react-dom/client';
import Navbar from './components/Navbar';
import PostCard from './components/PostCard';

const buildPostCardProps = (el) => ({
    id: el.getAttribute('data-id'),
    title: el.getAttribute('data-title'),
    category: el.getAttribute('data-category'),
    date: el.getAttribute('data-date'),
    excerpt: el.getAttribute('data-excerpt'),
    likes: el.getAttribute('data-likes'),
    comments: el.getAttribute('data-comments'),
    shares: el.getAttribute('data-shares'),
    userHasLiked: el.getAttribute('data-user-has-liked') === 'true',
    detailUrl: el.getAttribute('data-detail-url'),
    toggleLikeUrl: el.getAttribute('data-toggle-like-url'),
    shareUrl: el.getAttribute('data-share-url'),
    logoUrl: el.getAttribute('data-logo-url'),
    isAuthenticated: el.getAttribute('data-is-authenticated') === 'true',
    csrfToken: el.getAttribute('data-csrf-token'),
});

const mountPostCards = (container = document) => {
    container.querySelectorAll('.react-post-root').forEach((el) => {
        if (el.dataset.reactMounted === 'true') {
            return;
        }

        el.dataset.reactMounted = 'true';
        const root = createRoot(el);
        root.render(<PostCard {...buildPostCardProps(el)} />);
    });
};

// 1. Mount the Navigation Bar
const navRootElement = document.getElementById('react-navbar-root');
if (navRootElement) {
    const username = navRootElement.getAttribute('data-username');
    const isAuthenticated = navRootElement.getAttribute('data-is-authenticated') === 'true';
    const isStaff = navRootElement.getAttribute('data-is-staff') === 'true';
    const logoUrl = navRootElement.getAttribute('data-logo-url');
    
    const urls = {
        home: navRootElement.getAttribute('data-url-home'),
        admin: navRootElement.getAttribute('data-url-admin'),
        awareness: navRootElement.getAttribute('data-url-awareness'),
        report: navRootElement.getAttribute('data-url-report'),
        myReports: navRootElement.getAttribute('data-url-my-reports'),
        login: navRootElement.getAttribute('data-url-login'),
        register: navRootElement.getAttribute('data-url-register'),
        logout: navRootElement.getAttribute('data-url-logout')
    };
    
    const csrfToken = navRootElement.getAttribute('data-csrf-token');

    const root = createRoot(navRootElement);
    root.render(
        <Navbar 
            username={username} 
            isAuthenticated={isAuthenticated} 
            isStaff={isStaff} 
            logoUrl={logoUrl}
            urls={urls}
            csrfToken={csrfToken}
        />
    );
}

// 2. Mount Verified Posts (Facebook Style)
mountPostCards();
window.mountBanglaCERTPostCards = mountPostCards;
