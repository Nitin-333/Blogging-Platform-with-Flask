from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class SearchForm(FlaskForm):
    """Simple search form."""
    q = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')
