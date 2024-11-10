from flask_wtf import FlaskForm
from wtforms import IntegerField,StringField, SubmitField, SelectField, FloatField,TextAreaField,PasswordField,FileField
from wtforms.validators import DataRequired, URL, Email, NumberRange
import pycountry

def get_country_choices():
    countries = list(pycountry.countries)
    # Create a list of (code, country name) tuples for the SelectField
    return [(country.alpha_2, country.name) for country in countries]

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    code = StringField('Code', validators=[DataRequired()])
    description = StringField('Description',validators=[DataRequired()])
    remarks = TextAreaField('Remarks')
    price = FloatField('Price', validators=[DataRequired(),NumberRange(min=0)])
    category = SelectField('Category')
    filename = FileField('Browse Image')
    submit_btn = SubmitField('Submit',render_kw={'class':'btn-md btn-warning'})

class AddtoCartForm(FlaskForm):
    qty = IntegerField('Quantity', validators=[DataRequired(),NumberRange(min=1)])
    submit_btn = SubmitField('Add to Cart')


class SearchForm(FlaskForm):
    keyword = StringField('Keyword')
    submit_btn = SubmitField('Search',render_kw={'class':'btn-sm btn-dark'})

class NewDescriptionForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    submit_btn = SubmitField('Submit',render_kw={'class':'btn-sm btn-dark'})

class ProductSearchForm(FlaskForm):
    keyword = StringField('Keyword')
    category = SelectField('Category')
    submit_btn = SubmitField('Search',render_kw={'class':'btn-sm btn-dark'})

class RegisterForm(FlaskForm):
    fname = StringField("First Name", validators=[DataRequired()])
    mname = StringField("Middle Name", validators=[DataRequired()])
    lname = StringField("Last Name", validators=[DataRequired()])
    address = TextAreaField("Address", validators=[DataRequired()])
    postal_code = StringField("ZipCode", validators=[DataRequired()])
    country = SelectField('Country',choices=get_country_choices(),default="PH")
    contact_no =  StringField("Contact No.", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(),Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")


class ProfileForm(FlaskForm):
    fname = StringField("First Name", validators=[DataRequired()])
    mname = StringField("Middle Name", validators=[DataRequired()])
    lname = StringField("Last Name", validators=[DataRequired()])
    address = TextAreaField("Address", validators=[DataRequired()])
    postal_code = StringField("ZipCode", validators=[DataRequired()])
    country = SelectField('Country',choices=get_country_choices(),default="PH")
    contact_no =  StringField("Contact No.", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(),Email()])
    password = PasswordField("Password")
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(),Email()], render_kw={"placeholder": "Email" })
    password = PasswordField("Password",validators=[DataRequired()], render_kw={"placeholder": "Password"  })
    submit = SubmitField("Log me in")


class ForgotPassForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(),Email()], render_kw={"placeholder": "Email" })
    submit_btn = SubmitField('Reset Password')


class CheckoutForm(FlaskForm):
    address = TextAreaField("Address", validators=[DataRequired()])
    postal_code = StringField("ZipCode", validators=[DataRequired()])
    country = SelectField('Country',choices=get_country_choices(),default="PH")
    submit = SubmitField("Register")

