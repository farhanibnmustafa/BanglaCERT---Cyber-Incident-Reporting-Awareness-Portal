import React from 'react';
import { ThumbsUp, MessageCircle, Share2, ShieldCheck, MoreHorizontal } from 'lucide-react';
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
    const [liked, setLiked] = React.useState(userHasLiked);
    const [likesCount, setLikesCount] = React.useState(Number(likes) || 0);
    const [isLikePending, setIsLikePending] = React.useState(false);
    const EXCERPT_LIMIT = 180;
    const isLongPost = excerpt.length > EXCERPT_LIMIT;
    const postAnchor = `#awareness-post-${id}`;
    const currentReturnUrl =
        typeof window !== 'undefined'
            ? `${window.location.pathname}${window.location.search}${postAnchor}`
            : detailUrl;

    const handleLikeSubmit = async (event) => {
        event.preventDefault();

        if (isLikePending) {
            return;
        }

        const form = event.currentTarget;
        setIsLikePending(true);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            if (!response.ok) {
                throw new Error(`Like request failed with status ${response.status}`);
            }

            const nextLiked = !liked;
            setLiked(nextLiked);
            setLikesCount((previousCount) => Math.max(0, previousCount + (nextLiked ? 1 : -1)));
        } catch (error) {
            form.submit();
        } finally {
            setIsLikePending(false);
        }
    };
    
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
                    <span>{likesCount}</span>
                </div>
                <div className="fb-stat-right">
                    <span>{comments} comments • {shares} shares</span>
                </div>
            </div>

            {/* Action Buttons Section */}
            <footer className="fb-post-actions">
                <div className="fb-action-buttons-grid">
                    {isAuthenticated ? (
                        <form method="post" action={toggleLikeUrl} onSubmit={handleLikeSubmit}>
                            <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
                            <input type="hidden" name="next" value={currentReturnUrl} />
                            <button
                                type="submit"
                                className={`fb-action-btn ${liked ? 'active' : ''}`}
                                aria-pressed={liked}
                                disabled={isLikePending}
                            >
                                <ThumbsUp size={18} />
                                <span>{liked ? 'Liked' : 'Like'}</span>
                            </button>
                        </form>
                    ) : (
                        <a href={`/accounts/login/?next=${encodeURIComponent(currentReturnUrl)}`} className="fb-action-btn">
                            <ThumbsUp size={18} />
                            <span>Like</span>
                        </a>
                    )}

                    <a href={detailUrl} className="fb-action-btn">
                        <MessageCircle size={18} />
                        <span>Comment</span>
                    </a>

                    <a href={detailUrl} className="fb-action-btn">
                        <Share2 size={18} />
                        <span>Share</span>
                    </a>
                </div>
            </footer>
        </article>
    );
};

export default PostCard;
