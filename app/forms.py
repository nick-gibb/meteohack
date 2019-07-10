from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

from ac_calc.data import get_ac_brands

choices = [(g, g) for g in get_ac_brands()]


class LoginForm(FlaskForm):
    postal = StringField('Postal code')
    years = StringField('Years [1959-2100]', default='1969, 2019, 2099')
    brand = SelectField('Air conditioner manufacturer', choices=choices)
    model = SelectField('Air conditioner model', choices=[('', '')])
    submit = SubmitField('Calculate')
