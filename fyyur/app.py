# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#
import traceback

import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for
)
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from forms import *
from flask_migrate import Migrate
from models import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

# This import and implementation of babel breaks on WindowsOS
# for some unknown reason.
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
    body = []  # Hold final list of data
    try:
        all_venues = Venue.query.all()
        locations = Venue.query.distinct(Venue.city, Venue.state).all()
        for location in locations:
            body.append({
                "city": location.city,
                "state": location.state,
                "venues": [{
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": len(get_shows(venue.id, 'venue', 'upcoming'))
                } for venue in all_venues if venue.city == location.city
                    and venue.state == location.state]
            })

    except Exception as e:
        print(f'Something went wrong with loading the Venue page: {traceback.format_exc(), e}')

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
    venue = None
    try:
        venue = Venue.query.get(venue_id)
        # Clean multi-value string data from database
        genre_list = venue.genres.replace('{', '').replace('}', '').split(',')
        venue.genres = genre_list
        venue.past_shows = get_shows(venue_id, 'venue', 'past')
        venue.past_shows_count = len(venue.past_shows)
        venue.upcoming_shows = get_shows(venue_id, 'venue', 'upcoming')
        venue.upcoming_shows_count = len(venue.upcoming_shows)
    except Exception as e:
        print(e)
    return render_template('pages/show_venue.html', venue=venue)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form, csrf_enabled=False)
    data = -1

    if form.validate():
        items = request.form.items()
        genres = request.form.getlist('genres')
        new_venue = Venue()

        error = True
        try:
            new_venue = set_model_attr(items, new_venue, genres)
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
    else:
        flash(form.errors)
        return render_template('forms/new_venue.html', form=form)

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
        print(e)
        db.session.rollback()
        flash(f'Venue could not be deleted.', 'error')

    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    data = []
    all_artists = Artist.query.all()
    for artist in all_artists:
        data.append({
            "id": artist.id,
            "name": artist.name
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
    artist = None
    try:
        artist = Artist.query.get(artist_id)
        # Clean multi-value string data from database
        genre_list = artist.genres.replace('{', '').replace('}', '').split(',')
        artist.genres = genre_list
        artist.past_shows = get_shows(artist_id, 'artist', 'past')
        artist.past_shows_count = len(artist.past_shows)
        artist.upcoming_shows = get_shows(artist_id, 'artist', 'upcoming')
        artist.upcoming_shows_count = len(artist.upcoming_shows)
    except Exception as e:
        print(e)

    return render_template('pages/show_artist.html', artist=artist)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    new_artist_details = request.form.items()
    genre_list = request.form.getlist('genres')

    try:
        artist = Artist.query.get(artist_id)
        artist = set_model_attr(new_artist_details, artist, genre_list)
        db.session.commit()
    except:
        db.session.rollback()
        print("A problem with updating the model occurred.")

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    new_venue_details = request.form.items()
    genre_list = request.form.getlist('genres')

    try:
        venue = Venue.query.get(venue_id)
        venue = set_model_attr(new_venue_details, venue, genre_list)
        db.session.commit()
    except:
        db.session.rollback()
        print("A problem with updating the model occurred.")

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form, csrf_enabled=False)
    if form.validate():

        items = request.form.items()
        genres = request.form.getlist('genres')
        new_artist = Artist()

        data = -1
        error = True
        try:
            new_artist = set_model_attr(items, new_artist, genres)
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
    else:
        flash(form.errors)
        return render_template('forms/new_artist.html', form=form)

    return render_template('pages/home.html', data=data)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []
    shows_query_result = db.session.query(shows_table) \
        .filter(shows_table.c.artist_id == Artist.id) \
        .all()
    print(shows_query_result)
    for results in shows_query_result:
        body = {}
        artist = Artist.query.get(results[1])   # artist_id

        body['artist_id'] = artist.id
        body['artist_name'] = artist.name
        body['artist_image_link'] = artist.image_link
        body['start_time'] = str(results[2])     # start time

        for x in artist.venues:
            body['venue_id'] = x.id
            body['venue_name'] = x.name
        data.append(body)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form, csrf_enabled=False)
    if form.validate():
        artist_id = -1
        venue_id = -1
        start_time = -1
        show_form_data = request.form.items()
        for fields in show_form_data:
            if 'artist' in fields[0]:
                artist_id = fields[1]
            elif 'venue' in fields[0]:
                venue_id = fields[1]
            else:
                start_time = fields[1]

        try:
            shows_table.c.venue_id = venue_id
            shows_table.c.artist_id = artist_id
            shows_table.c.start_time = start_time
            db.session.commit()
            flash('Show was successfully listed!')
        except Exception as e:
            flash('Show was not listed.')
            print(f'There was an issue with inserting the show: {e}')
    else:
        flash("There was an issue with your form.")
        render_template('forms/new_show.html', form=form)

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


def set_model_attr(form_obj, model_obj, genre_list):
    try:
        for k, v in form_obj:
            if k == 'genres':
                setattr(model_obj, k, genre_list)
                continue
            setattr(model_obj, k, v)
    except Exception as e:
        print(f'An error occurred with parsing the genre list: {e}')
    return model_obj


# Get an id (Venue or Artist), filter condition based on "past or present" show_type, and based on model type give \
# back the right body
def get_shows(model_id, model_type, show_type):
    shows_raw = None
    body = []

    try:
        if show_type.lower() == 'past':
            shows_raw = db.session.query(Venue, Artist, shows_table.c.start_time) \
                .select_from(shows_table) \
                .join(Artist) \
                .filter(shows_table.c.venue_id == Venue.id) \
                .filter(shows_table.c.artist_id == Artist.id) \
                .filter(shows_table.c.start_time < datetime.now()) \
                .all()
        elif show_type.lower() == 'upcoming':
            shows_raw = db.session.query(Venue, Artist, shows_table.c.start_time) \
                .select_from(shows_table) \
                .join(Artist) \
                .filter(shows_table.c.venue_id == Venue.id) \
                .filter(shows_table.c.artist_id == Artist.id) \
                .filter(shows_table.c.start_time > datetime.now()) \
                .all()

        # (Venue, Artist, start_time)
        for results in shows_raw:
            past_shows = {}
            venue_id = results[0].id
            artist_id = results[1].id
            start_time = results[2]

            # Based on how jinja template and show tiles are arranged.
            # Shows via Venue want artist data and via Artist want venue
            if model_type.lower() == 'venue' and venue_id == model_id:
                artist = Artist.query.get(artist_id)
                past_shows['artist_id'] = artist.id
                past_shows['artist_name'] = artist.name
                past_shows['artist_image_link'] = artist.image_link
                past_shows['start_time'] = str(start_time)

            elif model_type.lower() == 'artist' and artist_id == model_id:
                venue = Venue.query.get(venue_id)
                past_shows['venue_id'] = venue.id
                past_shows['venue_name'] = venue.name
                past_shows['venue_image_link'] = venue.image_link
                past_shows['start_time'] = str(start_time)
            if bool(past_shows):
                body.append(past_shows)

    except Exception as e:
        print("An issue with db.session.query() occurred.")
        print(traceback.format_exc(), e)
    return body

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
