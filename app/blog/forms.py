from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class PostForm(FlaskForm):
    """Form for creating and editing blog posts."""
    title = StringField('Post Title', validators=[DataRequired(), Length(min=3, max=200)])
    summary = TextAreaField('Short Summary', validators=[Optional(), Length(max=300)])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    tags = StringField('Tags (comma-separated, e.g. python, flask, tutorial)', validators=[Optional(), Length(max=200)])
    content = TextAreaField('Article Content (Markdown supported)', validators=[DataRequired()])
    is_published = BooleanField('Publish post', default=True)
    submit = SubmitField('Save Article')

class CommentForm(FlaskForm):
    """Form for adding comments on a blog post."""
    content = TextAreaField(
        'Write a comment...',
        validators=[
            DataRequired(message='Comment cannot be empty.'),
            Length(min=2, max=2000, message='Comment must be between 2 and 2000 characters.')
        ]
    )
    submit = SubmitField('Submit Comment')
