from app.extensions import db
from app.models import User, Post, Category, Tag, Comment

def test_user_password_hashing(app):
    """Test user password hashing and verification."""
    user = User(username='security_test', email='sec@example.com')
    user.set_password('SecretP@ss1')
    assert user.password_hash is not None
    assert user.password_hash != 'SecretP@ss1'
    assert user.check_password('SecretP@ss1') is True
    assert user.check_password('WrongPass') is False

def test_user_avatar(app):
    """Test avatar URL generation."""
    user = User(username='sammy', email='sammy@example.com')
    avatar_url = user.avatar(64)
    assert 'gravatar.com/avatar/' in avatar_url
    assert 's=64' in avatar_url

def test_post_slug_generation_and_uniqueness(app, test_user):
    """Test unique slug generation and collision handling."""
    with app.app_context():
        p1 = Post(
            title='Clean Architecture Patterns',
            content='Content for p1',
            author_id=test_user.id
        )
        db.session.add(p1)
        db.session.commit()
        assert p1.slug == 'clean-architecture-patterns'

        p2 = Post(
            title='Clean Architecture Patterns',
            content='Content for p2',
            author_id=test_user.id
        )
        p2.slug = Post.generate_unique_slug(p2.title)
        db.session.add(p2)
        db.session.commit()
        assert p2.slug == 'clean-architecture-patterns-1'

def test_post_sanitization_xss_protection(app, test_user):
    """Test that malicious HTML/scripts are sanitized by bleach."""
    with app.app_context():
        malicious_content = "Hello <script>alert('hacked');</script> <img src=x onerror=alert(1)> <b>World</b>"
        post = Post(
            title='XSS Test Article',
            content=malicious_content,
            author_id=test_user.id
        )
        post.render_content()
        # Script tags and dangerous attributes like onerror must be stripped
        assert '<script>' not in post.content_html
        assert '</script>' not in post.content_html
        assert 'onerror' not in post.content_html
        assert '<b>World</b>' in post.content_html or '<strong>World</strong>' in post.content_html

def test_post_reading_time(app, test_user):
    """Test post reading time calculation."""
    post = Post(
        title='Quick Post',
        content='word ' * 450,
        author_id=test_user.id
    )
    # 450 words / 200 words per minute ~ 2 minutes
    assert post.reading_time == 2

def test_tag_and_category_relationships(app, test_user):
    """Test post association with categories and tags."""
    with app.app_context():
        cat = Category(name='DevOps', slug='devops')
        t1 = Tag(name='kubernetes', slug='kubernetes')
        t2 = Tag(name='ansible', slug='ansible')
        db.session.add_all([cat, t1, t2])
        db.session.commit()

        post = Post(
            title='Deploying with Kubernetes',
            content='K8s guide...',
            author_id=test_user.id,
            category_id=cat.id
        )
        post.tags.extend([t1, t2])
        db.session.add(post)
        db.session.commit()

        # Query back
        saved_post = Post.query.filter_by(title='Deploying with Kubernetes').first()
        assert saved_post.category.name == 'DevOps'
        assert len(saved_post.tags) == 2
        assert 'kubernetes' in [t.name for t in saved_post.tags]

def test_comment_cascade_deletion(app, test_user):
    """Test that deleting a post cascades and removes its comments."""
    with app.app_context():
        post = Post(
            title='Cascade Test Post',
            content='Some post content for cascade testing',
            author_id=test_user.id
        )
        db.session.add(post)
        db.session.commit()

        comment = Comment(
            content='Great writeup!',
            post_id=post.id,
            author_id=test_user.id
        )
        db.session.add(comment)
        db.session.commit()
        comment_id = comment.id

        assert db.session.get(Comment, comment_id) is not None

        # Delete post
        db.session.delete(post)
        db.session.commit()

        # Comment must be cascade deleted
        assert db.session.get(Comment, comment_id) is None
