from datetime import datetime, timezone
import bleach
from app.extensions import db

ALLOWED_COMMENT_TAGS = ['b', 'i', 'strong', 'em', 'code', 'pre', 'p', 'br', 'blockquote']

class Comment(db.Model):
    """Comment model for blog posts."""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    content_html = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Foreign Keys
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    def __init__(self, **kwargs):
        super(Comment, self).__init__(**kwargs)
        if self.content:
            self.render_content()

    def render_content(self):
        """Sanitize comment content."""
        clean_text = bleach.clean(
            self.content.replace('\n', '<br>'),
            tags=ALLOWED_COMMENT_TAGS,
            strip=True
        )
        self.content_html = clean_text

    def __repr__(self):
        return f"<Comment {self.id} on Post {self.post_id}>"
