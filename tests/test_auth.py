from app.models import User

def test_register_success(client, app):
    """Test successful user registration."""
    response = client.post(
        '/auth/register',
        data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Congratulations! Your account has been created' in response.data

    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'
        assert user.check_password('SecurePassword123!') is True

def test_register_duplicate_username(client, test_user):
    """Test registration failure with existing username."""
    response = client.post(
        '/auth/register',
        data={
            'username': test_user.username,
            'email': 'different@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }
    )
    assert response.status_code == 200
    assert b'This username is already taken' in response.data

def test_register_duplicate_email(client, test_user):
    """Test registration failure with existing email."""
    response = client.post(
        '/auth/register',
        data={
            'username': 'differentuser',
            'email': test_user.email,
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }
    )
    assert response.status_code == 200
    assert b'An account with this email address already exists' in response.data

def test_login_and_logout(client, auth, test_user):
    """Test user login with valid credentials and subsequent logout."""
    # Login with username
    res = auth.login(login_id='johndoe', password='Password123!')
    assert res.status_code == 200
    assert b'Welcome back, johndoe!' in res.data
    assert b'Write Post' in res.data

    # Logout
    res_logout = auth.logout()
    assert res_logout.status_code == 200
    assert b'You have been logged out successfully' in res_logout.data

def test_login_with_email(client, auth, test_user):
    """Test login with email address."""
    res = auth.login(login_id=test_user.email, password='Password123!')
    assert res.status_code == 200
    assert b'Welcome back, johndoe!' in res.data

def test_login_invalid_password(client, auth, test_user):
    """Test login failure with wrong password."""
    res = auth.login(login_id='johndoe', password='WrongPassword!')
    assert res.status_code == 200
    assert b'Invalid username/email or password' in res.data

def test_user_profile_page(client, test_user, test_post):
    """Test viewing user profile page and their authored articles."""
    response = client.get(f'/auth/user/{test_user.username}')
    assert response.status_code == 200
    assert test_user.username.encode() in response.data
    assert test_post.title.encode() in response.data

def test_edit_profile(client, auth, test_user):
    """Test editing profile while authenticated."""
    auth.login()
    response = client.post(
        '/auth/edit-profile',
        data={
            'username': 'johndoe',
            'email': 'johndoe_updated@example.com',
            'bio': 'Updated author bio.'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Your profile changes have been saved' in response.data
    assert b'Updated author bio.' in response.data

def test_change_password(client, auth, test_user, app):
    """Test changing user password."""
    auth.login()
    response = client.post(
        '/auth/change-password',
        data={
            'current_password': 'Password123!',
            'new_password': 'BrandNewPassword123!',
            'confirm_new_password': 'BrandNewPassword123!'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Your password has been updated successfully' in response.data

    with app.app_context():
        u = User.query.filter_by(username='johndoe').first()
        assert u.check_password('BrandNewPassword123!') is True
