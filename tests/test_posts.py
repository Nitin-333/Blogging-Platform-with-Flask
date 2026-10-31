from app.extensions import db
from app.models import Post

def test_create_post_authenticated(client, auth, test_user, test_category, app):
    """Test creating a blog post while authenticated."""
    auth.login()
    response = client.post(
        '/post/new',
        data={
            'title': 'Test Driven Development in Python',
            'summary': 'A practical guide to pytest and mocks.',
            'category_id': test_category.id,
            'tags': 'testing, python, pytest',
            'content': 'Write your tests first, then write your code.',
            'is_published': 'y'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Your blog post has been created!' in response.data
    assert b'Test Driven Development in Python' in response.data

    with app.app_context():
        post = Post.query.filter_by(title='Test Driven Development in Python').first()
        assert post is not None
        assert post.author_id == test_user.id
        assert post.slug == 'test-driven-development-in-python'
        assert len(post.tags) == 3

def test_create_post_unauthenticated_redirects(client):
    """Test that unauthenticated post creation redirects to login."""
    response = client.get('/post/new')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']

def test_view_post_increments_views(client, test_post, app):
    """Test viewing a post increments its view counter."""
    with app.app_context():
        initial_views = db.session.get(Post, test_post.id).views

    response = client.get(f'/post/{test_post.slug}')
    assert response.status_code == 200
    assert test_post.title.encode() in response.data

    with app.app_context():
        updated_views = db.session.get(Post, test_post.id).views
        assert updated_views == initial_views + 1

def test_edit_post_by_author(client, auth, test_post, app):
    """Test post author editing their post."""
    auth.login()
    response = client.post(
        f'/post/{test_post.slug}/edit',
        data={
            'title': 'Updated Intro to Flask Framework',
            'summary': 'Updated summary text.',
            'category_id': test_post.category_id,
            'tags': 'flask, microframework',
            'content': 'Updated content with **bold** text.',
            'is_published': 'y'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Your blog post has been updated.' in response.data
    assert b'Updated Intro to Flask Framework' in response.data

    with app.app_context():
        p = db.session.get(Post, test_post.id)
        assert p.title == 'Updated Intro to Flask Framework'

def test_edit_post_by_unauthorized_user_forbidden(client, auth, second_user, test_post):
    """Test non-author cannot edit someone else's post."""
    auth.login(login_id='janedoe', password='Password123!')
    response = client.get(f'/post/{test_post.slug}/edit')
    assert response.status_code == 403

def test_edit_post_by_admin(client, auth, test_admin, test_post):
    """Test admin can edit any user's post."""
    auth.login(login_id='adminuser', password='AdminPass123!')
    response = client.get(f'/post/{test_post.slug}/edit')
    assert response.status_code == 200

def test_delete_post_by_author(client, auth, test_post, app):
    """Test deleting post by author."""
    auth.login()
    response = client.post(f'/post/{test_post.slug}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'has been deleted' in response.data

    with app.app_context():
        assert Post.query.filter_by(slug=test_post.slug).first() is None

def test_delete_post_unauthorized_forbidden(client, auth, second_user, test_post):
    """Test non-author cannot delete someone else's post."""
    auth.login(login_id='janedoe', password='Password123!')
    response = client.post(f'/post/{test_post.slug}/delete')
    assert response.status_code == 403
