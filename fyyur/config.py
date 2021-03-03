import os
SECRET_KEY = os.urandom(32)
SQLALCHEMY_TRACK_MODIFICATIONS = False
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
SQLALCHEMY_DATABASE_URI = 'postgres://db_user:test@localhost:5432/fyyur'
