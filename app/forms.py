from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
import pandas as pd
filename = "data/010_room_air_conditioners_climatiseurs_individuels/010_Data_Données.csv"
acs = pd.read_csv(filename, encoding='cp1252')
brands = acs["BRAND_NAME"].unique().tolist()

choices = [(g, g) for g in brands]


class LoginForm(FlaskForm):
    postal = StringField('Postal code', validators=[DataRequired()])
    air_con = SelectField('Air conditioner brand', validators=[
                          DataRequired()], choices=choices)
    model = SelectField('Model', validators=[
                        DataRequired()], choices=[('', '')])
    submit = SubmitField('Submit')
