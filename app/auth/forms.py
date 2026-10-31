from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from flask_login import current_user
from app.models import User

class LoginForm(FlaskForm):
    """User login form."""
    login_id = StringField('Username or Email', validators=[DataRequired(), Length(min=3, max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """User registration form."""
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(min=3, max=30),
            Regexp(r'^[a-zA-Z0-9_]+$', message='Username must contain only letters, numbers, and underscores.')
        ]
    )
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=6, message='Password must be at least 6 characters long.')
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match.')
        ]
    )
    submit = SubmitField('Create Account')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError('This username is already taken. Please choose another.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError('An account with this email address already exists.')

class EditProfileForm(FlaskForm):
    """Edit user profile form."""
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(min=3, max=30),
            Regexp(r'^[a-zA-Z0-9_]+$', message='Username must contain only letters, numbers, and underscores.')
        ]
    )
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    bio = TextAreaField('Bio / About Me', validators=[Length(max=500)])
    submit = SubmitField('Save Profile')

    def validate_username(self, field):
        if field.data.strip() != current_user.username:
            if User.query.filter_by(username=field.data.strip()).first():
                raise ValidationError('This username is already in use.')

    def validate_email(self, field):
        if field.data.strip().lower() != current_user.email:
            if User.query.filter_by(email=field.data.strip().lower()).first():
                raise ValidationError('This email is already associated with an account.')

class ChangePasswordForm(FlaskForm):
    """Change password form."""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField(
        'New Password',
        validators=[DataRequired(), Length(min=6, message='Password must be at least 6 characters long.')]
    )
    confirm_new_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords must match.')]
    )
    submit = SubmitField('Update Password')
