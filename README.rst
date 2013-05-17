Bridback demo app
=================

Installation
------------

Cloning the project::

    git clone git://github.com/Birdback/demo.git ~/demo
    cd demo

Setup virtual environment::

    virtualenv env --python=python2
    source env/bin/activate

Install requirements::

    pip install requirements.txt


Configuration::

    export SECRET_KEY=myawesomesecret
    export DATABASE_URL=
    export API_APP_URL=/my-team/apps/my-app/
    export API_ID=myappplicationid
    export API_SECRET=myappplicationsecret
    export MAIL_SERVER=my.smtp.server
    export MAIL_USERNAME=my@username.tld
    export MAIL_PASSWORD=mypassword
    export MAIL_DEFAULT_SENDER=my@username.tld


Deployment
----------

You can quickly deploy the app on heroku::

    heroku create --region eu
    heroku config:set SECRET_KEY=myawesomesecret
    heroku config:set DATABASE_URL=
    heroku config:set API_APP_URL=/my-team/apps/my-app/
    heroku config:set API_ID=myappplicationid
    heroku config:set API_SECRET=myappplicationsecret
    heroku config:set MAIL_SERVER=my.smtp.server
    heroku config:set MAIL_USERNAME=my@username.tld
    heroku config:set MAIL_PASSWORD=mypassword
    heroku config:set MAIL_DEFAULT_SENDER=my@username.tld

Don't forget to set the ``transaction hook`` within you application settings.
