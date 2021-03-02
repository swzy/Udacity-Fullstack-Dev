# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

# Table should probably have a start time
shows = db.Table('shows',
                 db.Column('venue_id', db.Integer, db.ForeignKey('venue.id'), primary_key=True),
                 db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), primary_key=True),
                 db.Column('start_time', db.DateTime, default=datetime.utcnow, nullable=False)
                 )


# Should probably have a past shows
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
    artists = db.relationship('Artist',
                              secondary=shows,
                              backref=db.backref('venues', lazy=True))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


# Should also probably have a past shows
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

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    ## I would've added a new locations table and denormalized the Venue one, but \
    ## there is too much overhead and potential headache in refactoring the hardcoded \
    ## view templates.

    # TODO: num_shows should be aggregated based on number of upcoming shows per venue.

    body = []  # Hold final list of data
    try:
        all_venues = Venue.query.all()
        location_list = [] # Keep tuples of cities "seen"; Need to initialize to enumerate
        for venue in all_venues:
            data_format = {
                "id": -1,
                "city": None,
                "state": None,
                "venues": [{
                    "id": None,
                    "name": None,
                    "num_upcoming_shows": 0
                }]
            }
            location_tuple = (venue.city, venue.state)

            if location_tuple not in location_list:
                data_format['id'] = len(location_list)
                location_list.append(location_tuple)
                # If location has not been seen, then we create a new body entry
                data_format['city'] = location_tuple[0]
                data_format['state'] = location_tuple[1]
                data_format['venues'][0] = {
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": 0
                }
                body.append(data_format)
            else:
                venue_to_add = {
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": 0
                }
                # If location has been seen, find the location entry and \
                # append the venue to the venues list, if it is not a duplicate
                location_index = location_list.index(location_tuple)

                for locations in body:
                    # After looking through body, checking for a dupe venue
                    # Because body and venue elements are unique, break if found.
                    if location_index == locations['id']:
                        for cnt, ven in enumerate(locations['venues']):
                            if venue.name == ven['name']:
                                break
                            elif venue.name != ven['name'] and cnt == len(locations['venues']) - 1:
                                locations['venues'].append(venue_to_add)
                        break

    except Exception as e:
        print(e)

    return render_template('pages/venues.html', areas=body)


@app.route('/venues/search', methods=['GET', 'POST'])
def search_venues():
    venue_list = []
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        all_venues = Venue.query.all()
        for venue in all_venues:
            if search_term.lower() in venue.name.lower():
                venue_list.append({
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": 0
                })

    response = {
        "count": len(venue_list),
        "data": venue_list
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # Need to fill upcoming/past shows - Might need to add a column, etc.
    # Hold on this until artist gets fleshed out more.

    try:
        venue = Venue.query.get(venue_id)
        # Clean multi-value string data from database
        genre_list = venue.genres.replace('{', '').replace('}', '').split(',')
        venue.genres = genre_list
    except Exception as e:
        print(e)
        # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
    return render_template('pages/show_venue.html', venue=venue)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

def set_model_attr(genre_list, form_obj, model_obj):
    try:
        for k, v in form_obj:
            if k == 'genres':
                setattr(model_obj, k, genre_list)
                continue
            setattr(model_obj, k, v)
    except Exception as e:
        print(f'An error occurred with parsing the genre list: {e}')
    return model_obj


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    items = request.form.items()
    genres = request.form.getlist('genres')
    new_venue = Venue()

    data = -1
    error = True
    try:
        new_venue = set_model_attr(genres, items, new_venue)
        error = False
    except Exception as e:
        print(f'Error with parsing occurred: {e}')

    if not error:
        try:
            db.session.add(new_venue)
            db.session.commit()
            data = new_venue
            flash(f'{request.form["name"]} was successfully listed!')
        except Exception as e:
            print(e)
            db.session.rollback()
            flash(f'Venue {request.form["name"]} could not be listed.', 'error')
        finally:
            db.session.close()

    return render_template('pages/home.html', data=data)


@app.route('/venues/<venue_id>', methods=['POST', 'DELETE'])
def delete_venue(venue_id):
    venue = Venue.query.get(venue_id)
    try:
        name = venue.name
        db.session.delete(venue)
        db.session.commit()
        flash(f'Venue {name} was successfully deleted.')
    except Exception as e:
        db.session.rollback()
        flash(f'Venue could not be deleted.', 'error')

    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    data = []
    all_artists = Artist.query.all()
    for artists in all_artists:
        data.append({
            "id": artists.id,
            "name": artists.name
        })
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    artist_list = []
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        all_artists = Artist.query.all()
        for artist in all_artists:
            if search_term.lower() in artist.name.lower():
                artist_list.append({
                    "id": artist.id,
                    "name": artist.name,
                    "num_upcoming_shows": 0
                })

    response = {
        "count": len(artist_list),
        "data": artist_list
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        # Clean multi-value string data from database
        genre_list = artist.genres.replace('{', '').replace('}', '').split(',')
        artist.genres = genre_list
    except Exception as e:
        print(e)

    return render_template('pages/show_artist.html', artist=artist)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = {
        "id": 4,
        "name": "Guns N Petals",
        "genres": ["Rock n Roll"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "326-123-5000",
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": "https://www.facebook.com/GunsNPetals",
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = {
        "id": 1,
        "name": "The Musical Hop",
        "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
        "address": "1015 Folsom Street",
        "city": "San Francisco",
        "state": "CA",
        "phone": "123-123-1234",
        "website": "https://www.themusicalhop.com",
        "facebook_link": "https://www.facebook.com/TheMusicalHop",
        "seeking_talent": True,
        "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
        "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    items = request.form.items()
    genres = request.form.getlist('genres')
    new_artist = Artist()

    data = -1
    error = True
    try:
        new_artist = set_model_attr(genres, items, new_artist)
        error = False
    except Exception as e:
        print(f'Error with parsing occurred: {e}')

    if not error:
        try:
            db.session.add(new_artist)
            db.session.commit()
            data = new_artist
            flash(f'{request.form["name"]} was successfully listed!')
        except Exception as e:
            print(e)
            db.session.rollback()
            flash(f'Artist {request.form["name"]} could not be listed.', 'error')
        finally:
            db.session.close()
    return render_template('pages/home.html', data=data)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    data = [{
        "venue_id": 1,
        "venue_name": "The Musical Hop",
        "artist_id": 4,
        "artist_name": "Guns N Petals",
        "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
        "start_time": "2019-05-21T21:30:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 5,
        "artist_name": "Matt Quevedo",
        "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
        "start_time": "2019-06-15T23:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-01T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-08T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-15T20:00:00.000Z"
    }]
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    # on successful db insert, flash success
    flash('Show was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
