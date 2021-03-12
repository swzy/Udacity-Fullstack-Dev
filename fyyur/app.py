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
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from models import *
from forms import VenueForm, ArtistForm, ShowForm

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
csrf = CSRFProtect(app)
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
                # Set comprehension
                "venues": [{
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows":
                        len([show for show in venue.shows
                             if show.start_time > datetime.now()])
                } for venue in all_venues if venue.city == location.city
                    and venue.state == location.state]
            })

    except Exception as e:
        print(f'Something went wrong with loading the Venue page: '
              f'{traceback.format_exc(), e}')

    return render_template('pages/venues.html', areas=body)


@app.route('/venues/search', methods=['GET', 'POST'])
def search_venues():
    venue_list = []
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
        possible_venues = Venue.query.filter(
            Venue.name.ilike(f'%{search_term}%'))
        for venue in possible_venues:
            venue_list.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows":
                    len([show for show in venue.shows
                        if show.start_time > datetime.now()])
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
        venue.genres = venue.genres.replace('{', '') \
            .replace('}', '') \
            .split(',')
        venue.past_shows = get_shows('venue', 'past', venue_id)
        venue.past_shows_count = len(venue.past_shows)
        venue.upcoming_shows = get_shows('venue', 'upcoming', venue_id)
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
    form = VenueForm(request.form)

    if form.validate():
        try:
            venue = Venue()
            form.populate_obj(venue)
            db.session.add(venue)
            db.session.commit()
            flash(f'{request.form["name"]} was successfully listed!')
        except ValueError as e:
            print(e)
            flash(f'Venue "{request.form["name"]}" could not be listed.',
                  'error')
        finally:
            db.session.close()

    else:
        flash(form.errors)
        return render_template('forms/new_venue.html', form=form)

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['POST', 'DELETE'])
def delete_venue(venue_id):
    venue = Venue.query.get(venue_id)
    try:
        name = venue.name
        db.session.delete(venue)
        db.session.commit()
        flash(f'Venue "{name}" was successfully deleted.')
    except Exception as e:
        print(e)
        db.session.rollback()
        flash(f'Venue could not be deleted.', 'error')

    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    all_artists = Artist.query.all()
    return render_template('pages/artists.html', artists=all_artists)


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
        artist.genres = artist.genres.replace('{', '') \
            .replace('}', '') \
            .split(',')
        artist.past_shows = get_shows('artist', 'past', artist_id)
        artist.past_shows_count = len(artist.past_shows)
        artist.upcoming_shows = get_shows('artist', 'upcoming', artist_id)
        artist.upcoming_shows_count = len(artist.upcoming_shows)
    except Exception as e:
        print(e)

    return render_template('pages/show_artist.html', artist=artist)


@app.route('/artists/<artist_id>', methods=['POST', 'DELETE'])
def delete_artist(artist_id):
    artist = Artist.query.get(artist_id)
    try:
        name = artist.name
        db.session.delete(artist)
        db.session.commit()
        flash(f'Artist {name} was successfully deleted.')
    except Exception as e:
        print(e)
        db.session.rollback()
        flash(f'Artist could not be deleted.', 'error')
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.filter(Artist.id == artist_id).first_or_404()
    form = ArtistForm(obj=artist)

    return render_template('forms/edit_artist.html',
                           form=form,
                           artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)

    if form.validate():
        try:
            existing_artist = Artist.query.get(artist_id)
            form.populate_obj(existing_artist)
            db.session.commit()
            flash(f'Artist was successfully updated.')
        except ValueError as e:
            print(e)
            flash(f'Artist could not be updated', 'error')
        finally:
            db.session.close()
    else:
        flash(form.errors)
        return render_template('forms/edit_artist.html',
                               form=form,
                               artist=Artist.query.get(artist_id))

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.filter(Venue.id == venue_id).first_or_404()
    form = VenueForm(obj=venue)

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)

    if form.validate():
        try:
            existing_venue = Venue.query.get(venue_id)
            form.populate_obj(existing_venue)
            db.session.commit()
            flash(f'Venue was successfully updated.')
        except ValueError as e:
            print(e)
            flash(f'Venue could not be updated', 'error')
        finally:
            db.session.close()
    else:
        flash(form.errors)
        return render_template('forms/edit_venue.html',
                               form=form,
                               venue=Venue.query.get(venue_id))

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)

    if form.validate():
        try:
            new_artist = Artist()
            form.populate_obj(new_artist)
            db.session.add(new_artist)
            db.session.commit()
            flash(f'{request.form["name"]} was successfully listed!')
        except ValueError as e:
            print(e)
            flash(f'Artist {request.form["name"]} could not be listed.',
                  'error')
        finally:
            db.session.close()
    else:
        flash(form.errors)
        return render_template('forms/new_artist.html', form=form)

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []
    shows_query_result = Show.query.all()
    for results in shows_query_result:
        data.append({
            "venue_id": results.venue_id,
            "venue_name":
                Venue.query
                .get(results.venue_id)
                .name,
            "artist_id": results.artist_id,
            "artist_name":
                Artist.query
                .get(results.artist_id)
                .name,
            "artist_image_link":
                Artist.query
                .get(results.artist_id)
                .image_link,
            "start_time": str(results.start_time)
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)

    if form.validate():
        try:
            new_show = Show()
            form.populate_obj(new_show)
            db.session.add(new_show)
            db.session.commit()
            flash('Show was successfully listed!')
        except ValueError as e:
            flash('Show was not listed.')
            print(f'There was an issue with inserting the show: {e}')
        finally:
            db.session.close()
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
        Formatter('%(asctime)s %(levelname)s: %(message)s'
                  '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


# Model type: past, upcoming
# Show type: venue, artist
# Model Id: From current page
def get_shows(model_type, show_type, model_id):
    shows_raw = None
    body = []
    try:
        if show_type == 'past':
            shows_raw = Show.query \
                .join(Artist) \
                .join(Venue) \
                .filter(Show.start_time < datetime.now()) \
                .all()
        elif show_type == 'upcoming':
            shows_raw = Show.query \
                .join(Artist) \
                .join(Venue) \
                .filter(Show.start_time > datetime.now()) \
                .all()
        for show in shows_raw:
            if model_type == 'venue' and show.venue_id == model_id:
                artist = Artist.query.get(show.artist_id)
                body.append({
                    "artist_id": artist.id,
                    "artist_name": artist.name,
                    "artist_image_link": artist.image_link,
                    "start_time": str(show.start_time)
                })
            elif model_type == 'artist' and show.artist_id == model_id:
                venue = Venue.query.get(show.venue_id)
                body.append({
                    "venue_id": venue.id,
                    "venue_name": venue.name,
                    "venue_image_link": venue.image_link,
                    "start_time": str(show.start_time)
                })
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
