from urllib.parse import urlsplit
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, EditProfileForm, ChangePasswordForm
from app.extensions import db
from app.models import User, Post

def is_safe_redirect_url(target):
    """Ensure next redirect target stays on the same host (prevents open redirect)."""
    if not target:
        return False
    ref_url = urlsplit(request.host_url)
    test_url = urlsplit(target)
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc or not test_url.netloc

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user account."""
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower()
        )
        user.set_password(form.password.data)
        
        # If this is the very first user, grant admin privileges
        if User.query.count() == 0:
            user.is_admin = True

        db.session.add(user)
        db.session.commit()
        flash('Congratulations! Your account has been created. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticate and log in an existing user."""
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.login_id.data.strip()
        # Look up by either email or username
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username/email or password. Please try again.', 'danger')
            return render_template('auth/login.html', title='Sign In', form=form)

        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome back, {user.username}!', 'success')

        next_page = request.args.get('next')
        if not next_page or not is_safe_redirect_url(next_page):
            next_page = url_for('blog.index')
        return redirect(next_page)

    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Log out current user."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('blog.index'))

@bp.route('/user/<username>')
def profile(username):
    """View public user profile and list their posts."""
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 6)

    # If viewing own profile or admin, show drafts too, otherwise only published
    query = user.posts
    if not (current_user.is_authenticated and (current_user.id == user.id or current_user.is_admin)):
        query = query.filter_by(is_published=True)

    pagination = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    posts = pagination.items

    return render_template(
        'auth/profile.html',
        title=f"{user.username}'s Profile",
        user=user,
        posts=posts,
        pagination=pagination
    )

@bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit current user's profile details."""
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data.strip()
        current_user.email = form.email.data.strip().lower()
        current_user.bio = form.bio.data.strip()
        db.session.commit()
        flash('Your profile changes have been saved.', 'success')
        return redirect(url_for('auth.profile', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio

    return render_template('auth/edit_profile.html', title='Edit Profile', form=form)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change current user's password."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated successfully.', 'success')
            return redirect(url_for('auth.profile', username=current_user.username))

    return render_template('auth/change_password.html', title='Change Password', form=form)
