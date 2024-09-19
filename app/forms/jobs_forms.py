from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired

class CreateJobForm(FlaskForm):
    """Form for jobs to create a new job listing."""
    title = StringField('Job Title', validators=[DataRequired()])
    description = TextAreaField('Job Description', validators=[DataRequired()])
    budget = StringField('Budget', validators=[DataRequired()])
    status = SelectField('Status', choices=[('open', 'Open'), ('closed', 'Closed')], validators=[DataRequired()])
    submit = SubmitField('Create Job')

class UpdateJobForm(FlaskForm):
    """Form for jobs to update an existing job listing."""
    title = StringField('Job Title', validators=[DataRequired()])
    description = TextAreaField('Job Description', validators=[DataRequired()])
    budget = StringField('Budget', validators=[DataRequired()])
    status = SelectField('Status', choices=[('open', 'Open'), ('closed', 'Closed')], validators=[DataRequired()])
    submit = SubmitField('Update Job')
