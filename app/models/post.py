import re
import bleach
import markdown
from datetime import datetime, timezone
from app.extensions import db

# Allowed tags and attributes for sanitizing rich text HTML
ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol',
    'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'hr',
    'br', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'span', 'del',
    'sup', 'sub'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'th': ['scope', 'colspan', 'rowspan'],
    'td': ['colspan', 'rowspan']
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

def slugify(text):
    """Convert arbitrary text into a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text or 'post'

# Many-to-Many Association Table between Post and Tag
post_tags = db.Table(
    'post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

class Category(db.Model):
    """Category model for grouping blog posts."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), default='')

    # Relationship to posts
    posts = db.relationship('Post', backref='category', lazy='dynamic')

    def __init__(self, name, description='', slug=None):
        self.name = name
        self.description = description
        self.slug = slug or slugify(name)

    def __repr__(self):
        return f"<Category {self.name}>"

class Tag(db.Model):
    """Tag model for labeling blog posts."""
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)

    def __init__(self, name, slug=None):
        self.name = name.strip()
        self.slug = slug or slugify(name)

    def __repr__(self):
        return f"<Tag {self.name}>"

class Post(db.Model):
    """Blog Post model."""
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    summary = db.Column(db.String(300), default='')
    content = db.Column(db.Text, nullable=False)
    content_html = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    is_published = db.Column(db.Boolean, default=True, index=True)
    views = db.Column(db.Integer, default=0)

    # Foreign Keys
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    tags = db.relationship(
        'Tag',
        secondary=post_tags,
        lazy='subquery',
        backref=db.backref('posts', lazy='dynamic')
    )
    comments = db.relationship(
        'Comment',
        backref='post',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='desc(Comment.created_at)'
    )

    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = self.generate_unique_slug(self.title)
        if self.content:
            self.render_content()

    @classmethod
    def generate_unique_slug(cls, title, post_id=None):
        """Generate a unique slug ensuring no collision."""
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        query = cls.query.filter_by(slug=slug)
        if post_id:
            query = query.filter(cls.id != post_id)
        while query.first():
            slug = f"{base_slug}-{counter}"
            counter += 1
            query = cls.query.filter_by(slug=slug)
            if post_id:
                query = query.filter(cls.id != post_id)
        return slug

    def render_content(self):
        """Render Markdown / HTML content and sanitize for safe rendering."""
        # Check if content looks already like HTML or Markdown
        # Markdown handles HTML tags directly, and extensions add extra capabilities
        html = markdown.markdown(
            self.content or '',
            extensions=['extra', 'codehilite', 'toc', 'nl2br']
        )
        self.content_html = bleach.clean(
            html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True
        )

    @property
    def reading_time(self):
        """Estimate reading time in minutes (approx 200 words/min)."""
        words = len(re.findall(r'\w+', self.content or ''))
        return max(1, round(words / 200))

    def tag_names_string(self):
        """Return tags as comma-separated string."""
        return ', '.join(tag.name for tag in self.tags)

    def __repr__(self):
        return f"<Post '{self.title}'>"
