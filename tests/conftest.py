import pytest
from app import create_app
from app.extensions import db
from app.models import User, Post, Category, Tag, Comment

@pytest.fixture
def app():
    """Create and configure a new app instance for each test suite."""
    test_app = create_app('testing')
    ctx = test_app.app_context()
    ctx.push()
    db.create_all()

    yield test_app

    db.session.remove()
    db.drop_all()
    ctx.pop()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def test_user(app):
    """Create a standard test user."""
    user = User(
        username='johndoe',
        email='johndoe@example.com',
        bio='Test bio for John Doe'
    )
    user.set_password('Password123!')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_admin(app):
    """Create an administrator user."""
    admin = User(
        username='adminuser',
        email='admin@example.com',
        bio='Platform admin',
        is_admin=True
    )
    admin.set_password('AdminPass123!')
    db.session.add(admin)
    db.session.commit()
    return admin

@pytest.fixture
def second_user(app):
    """Create a second standard user to test permissions."""
    user = User(
        username='janedoe',
        email='janedoe@example.com',
        bio='Second test user'
    )
    user.set_password('Password123!')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_category(app):
    """Create a sample category."""
    cat = Category(
        name='Tutorials',
        slug='tutorials',
        description='Step by step technical guides'
    )
    db.session.add(cat)
    db.session.commit()
    return cat

@pytest.fixture
def test_tag(app):
    """Create a sample tag."""
    tag = Tag(name='flask', slug='flask')
    db.session.add(tag)
    db.session.commit()
    return tag

@pytest.fixture
def test_post(app, test_user, test_category, test_tag):
    """Create a sample published post."""
    post = Post(
        title='Intro to Flask Framework',
        slug='intro-to-flask-framework',
        summary='A guide to starting with Flask.',
        content='Flask is a lightweight **WSGI** web application framework in Python.',
        author_id=test_user.id,
        category_id=test_category.id,
        is_published=True
    )
    post.render_content()
    post.tags.append(test_tag)
    db.session.add(post)
    db.session.commit()
    return post

class AuthActions:
    """Helper class to log in and out inside test client."""
    def __init__(self, client):
        self._client = client

    def login(self, login_id='johndoe', password='Password123!'):
        return self._client.post(
            '/auth/login',
            data={'login_id': login_id, 'password': password},
            follow_redirects=True
        )

    def logout(self):
        return self._client.get('/auth/logout', follow_redirects=True)

@pytest.fixture
def auth(client):
    return AuthActions(client)
