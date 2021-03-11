from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

# shows_table = db.Table('shows',
#      db.Column('venue_id', db.Integer, db.ForeignKey('venue.id'), primary_key=True),
#      db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), primary_key=True),
#      db.Column('start_time', db.DateTime, default=datetime.utcnow, nullable=False)
#      )

class Show(db.Model):
    __tablename__ = 'shows'
    venue_id = db.Column('venue_id', db.Integer, db.ForeignKey('venue.id'), primary_key=True)
    artist_id = db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), primary_key=True),
    start_time = db.Column('start_time', db.DateTime, default=datetime.utcnow, nullable=False)
    venue = db.relationship('Venue', backref='venue_shows')
    artist = db.relationship('Artist', backref='artist_shows')

class Venue(db.Model):
    __tablename__ = 'venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String)
    website = db.Column(db.String)
    seeking_talent = db.Column(db.String)
    seeking_description = db.Column(db.String)
    # artists = db.relationship('Artist',
    #                           secondary='shows',
    #                           backref=db.backref('venues', lazy='joined'))
    artists = db.relationship('Show')

class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String)
    seeking_venue = db.Column(db.String)
    seeking_description = db.Column(db.String)
    # venues = db.relationship('Venue',
    #                          secondary=shows_table,
    #                          backref=db.backref('artists', lazy='joined'))
    venues = db.relationship('Show')
