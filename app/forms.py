from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    postal = StringField('Postal code', validators=[DataRequired()])
    submit = SubmitField('Submit')
