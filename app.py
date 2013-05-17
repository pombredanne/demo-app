# -*- coding: utf-8 -*-
import os
import requests
from datetime import datetime

from flask import Flask, render_template, request, flash, abort, redirect, \
    url_for

from baluhn import verify
from wtforms import Form as BaseForm, FormField, TextField, validators
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.dashed.admin import Admin
from flask.ext.dashed.ext.sqlalchemy import ModelAdminModule
from flask.ext.mail import Mail, Message
from birdback.xauth import Client


app = Flask(__name__)

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY=os.environ.get('SECRET_KEY'),
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL'),
    API_URL=os.environ.get('API_URL', 'https://api.birdback.com'),
    API_APP_URL=os.environ.get('API_APP_URL'),
    API_SECRET=os.environ.get('API_SECRET'),
    API_ID=os.environ.get('API_ID'),
    MAIL_SERVER=os.environ.get('MAIL_SERVER'),
    MAIL_PORT=os.environ.get('MAIL_PORT', 25),
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER'),
))


db = SQLAlchemy(app)
mail = Mail(app)


class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), nullable=False, unique=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    profile_id = db.Column(db.Integer, nullable=False, unique=True)
    # Postgres UUID can be used here:
    card_token = db.Column(db.String(255), nullable=False, unique=True)


class Transaction(db.Model):
    # Postgres UUID can be used here:
    id = db.Column(db.String(255), primary_key=True)
    subscriber_id = db.Column(db.Integer, db.ForeignKey('subscriber.id'),
        nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    subscriber = db.relationship('Subscriber')


session = db.session


class Form(BaseForm):
    def set_errors(self, errors):
        for field_name in errors:
            field = self._fields[field_name]
            if field.type == 'FormField':
                field.set_errors(errors[field_name])
            else:
                field.errors = errors[field_name]

    def validate_number(self, field):
        error = validators.ValidationError("Invalid card number.")
        try:
            if not verify(field.data.replace('-', '')):
                raise error
        except:
            raise error


class CardForm(Form):
    number = TextField(validators=[validators.required()])


class ProfileForm(Form):
    email = TextField(validators=[validators.required()])
    first_name = TextField(validators=[validators.required()])
    last_name = TextField(validators=[validators.required()])
    card = FormField(CardForm, separator='_')


@app.route('/', methods=['GET', 'POST'])
def home():
    form = ProfileForm(request.form)
    if request.method == 'POST':
        if form.validate():
            # Authenticate on Birdback API
            client = Client(app.config.get('API_URL'), '/auth/token/',
                consumer_id=app.config.get('API_ID'),
                consumer_secret=app.config.get('API_SECRET'),)
            client.authenticate()
            if not client.token_id:
                abort(403, 'Birdback API authentication failed.')
            # Push profile to Birdback API
            r = client.post('%sprofiles/' % app.config.get('API_APP_URL'),
                data=dict(
                    email=request.form['email'],
                    first_name=request.form['first_name'],
                    last_name=request.form['last_name'],
                    card_number=request.form['card_number'],
                ))
            if r.status_code == 201:
                # Create a new subscriber from Birdback profile id
                subscriber = Subscriber()
                subscriber.profile_id = r.json()['id']
                subscriber.card_token = r.json()['cards'][0]['token']
                subscriber.email = request.form['email']
                subscriber.first_name = request.form['first_name']
                subscriber.last_name = request.form['last_name']
                session.add(subscriber)
                session.commit()
                flash('You have successfully been registered.', 'success')
                return redirect(url_for('home'))
            elif r.status_code == 422:
                errors = r.json().get('errors')
                form.set_errors(errors)
                flash(r.json().get('message'), 'error')
                mail.send(Message('New transaction', body, recipients=[subscriber.email]))
        else:
            flash('Registration failed due to errors.', 'error')
    return render_template('home.html', form=form)


@app.route('/transaction/', methods=['POST'])
def transaction():
    """Handles transaction hook.
    """
    data = request.json
    id = data['id']
    amount = data['amount']
    currency = data['currency']['name']
    card_token = data['card']['token']
    subscriber = Subscriber.query.filter_by(card_token=card_token).one()
    transaction = Transaction()
    transaction.id = id
    transaction.amount = amount
    transaction.subscriber = subscriber
    session.add(transaction)
    session.commit()
    body = "You just made a %s %s transaction in one of our stores. " % \
        (str(amount), currency)
    mail.send(Message('New transaction', body=body,
        recipients=[subscriber.email]))
    return 'ok', 201


# Admin
admin = Admin(app)


class SubscriberModule(ModelAdminModule):
    model = Subscriber
    db_session = session


class TransactionModule(ModelAdminModule):
    model = Transaction
    db_session = session


admin.register_module(SubscriberModule, '/subscribers/', 'subscribers',
    'subscribers')
admin.register_module(TransactionModule, '/transactions/', 'transaction',
    'transactions')
