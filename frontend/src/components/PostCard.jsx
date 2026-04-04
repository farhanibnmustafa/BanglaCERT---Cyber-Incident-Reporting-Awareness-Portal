import React from 'react';
import { ThumbsUp, MessageCircle, Share2, ShieldCheck, MoreHorizontal, ExternalLink } from 'lucide-react';
import './PostCard.css';

const PostCard = ({ 
    id,
    title, 
    category, 
    date, 
    excerpt, 
    likes, 
    comments, 
    shares, 
    userHasLiked,
    detailUrl,
    toggleLikeUrl,
    shareUrl,
    logoUrl,
    isAuthenticated,
    csrfToken
}) => {
    const [isExpanded, setIsExpanded] = React.useState(false);
    const EXCERPT_LIMIT = 180;
    const isLongPost = excerpt.length > EXCERPT_LIMIT;
    
    // Determine what text to show based on expansion state
    const displayText = isExpanded ? excerpt : excerpt.slice(0, EXCERPT_LIMIT);

    return (
        <article className="fb-post-card">
            {/* Header Section */}
            <header className="fb-post-header">
                <div className="fb-post-author-info">
                    <img src={logoUrl} alt="BanglaCERT" className="fb-post-avatar" />
                    <div className="fb-post-meta-text">
                        <div className="fb-post-author-name">
                            <span>BanglaCERT Verified Signal</span>
                            <ShieldCheck size={14} className="verified-badge-icon" />
                        </div>
                        <time className="fb-post-time">{date}</time>
                    </div>
                </div>
                <button className="fb-post-more-btn" aria-label="More options">
                    <MoreHorizontal size={20} />
                </button>
            </header>

            {/* Content Section */}
            <div className="fb-post-content">
                <h2 className="fb-post-title">
                    <a href={detailUrl}>{title}</a>
                </h2>
                <div className="fb-post-category-tag">
                    {category}
                </div>
                <p className="fb-post-excerpt">
                    {displayText}
                    {isLongPost && !isExpanded && "..."}
                </p>
                
                {isLongPost && (
                    <button 
                        className="fb-see-more-btn" 
                        onClick={() => setIsExpanded(!isExpanded)}
                    >
                        {isExpanded ? 'See Less' : 'See More'}
                    </button>
                )}
            </div>

            {/* Visual Stats Section */}
            <div className="fb-post-stats">
                <div className="fb-stat-left">
                    <div className="fb-stat-icon-group">
                        <div className="fb-stat-icon-circle like">
                            <ThumbsUp size={10} fill="white" stroke="white" />
                        </div>
                    </div>
                    <span>{likes}</span>
                </div>
                <div className="fb-stat-right">
                    <span>{comments} comments • {shares} shares</span>
                </div>
            </div>

            {/* Action Buttons Section */}
            <footer className="fb-post-actions">
                <div className="fb-action-buttons-grid">
                    {isAuthenticated ? (
                        <form method="post" action={toggleLikeUrl}>
                            <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
                            <button type="submit" className={`fb-action-btn ${userHasLiked ? 'active' : ''}`}>
                                <ThumbsUp size={18} />
                                <span>{userHasLiked ? 'Liked' : 'Like'}</span>
                            </button>
                        </form>
                    ) : (
                        <a href={`/accounts/login/?next=${window.location.pathname}`} className="fb-action-btn">
                            <ThumbsUp size={18} />
                            <span>Like</span>
                        </a>
                    )}

                    <a href={detailUrl} className="fb-action-btn">
                        <MessageCircle size={18} />
                        <span>Comment</span>
                    </a>

                    <form method="post" action={shareUrl}>
                        <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
                        <button type="submit" className="fb-action-btn">
                            <Share2 size={18} />
                            <span>Share</span>
                        </button>
                    </form>

                    <a href={detailUrl} className="fb-action-btn fb-action-link-btn" title="Open post">
                        <ExternalLink size={18} />
                    </a>
                </div>
            </footer>
        </article>
    );
};

export default PostCard;
