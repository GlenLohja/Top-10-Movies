from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from typing import Callable
from sqlalchemy import desc

MOVIE_DB_API_KEY = 'f0817c78710cc959164156d1e0155a2a'
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

class MySQLAlchemy(SQLAlchemy):
    Column: Callable
    String: Callable
    Integer: Callable
    Float: Callable


db = MySQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)
db.create_all()

class Edit(FlaskForm):
    rating = StringField(label='Your rating Out of 10 e.g. 7.5')
    review = StringField(label='Your review')
    done = SubmitField(label='Done')

class AddForm(FlaskForm):
    title = StringField(label='Movie Title', validators=[DataRequired()])
    add_movie=SubmitField(label='Add Movie')


@app.route("/")
def home():
    all_movies =Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies)-i
    return render_template("index.html", movies=all_movies)

@app.route('/edit', methods=['POST', 'GET'])
def edit():
    edit_form = Edit()
    id = request.args.get('id')
    movie_to_update = Movie.query.get(id)
    if edit_form.validate_on_submit():
        movie_to_update.rating = float(edit_form.rating.data)
        movie_to_update.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html',movie=movie_to_update, form=edit_form)

@app.route('/delete')
def delete():
    id = request.args.get('id')
    movie_to_delete = Movie.query.get(id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/add', methods=['POST','GET'])
def add():
    add_form= AddForm()
    if add_form.validate_on_submit():
        movie_title = add_form.title.data
        response = requests.get(url=MOVIE_DB_SEARCH_URL, params={'query': movie_title, 'api_key': MOVIE_DB_API_KEY})
        all_movies = response.json()['results']
        return render_template('select.html', movies=all_movies)
    return render_template('add.html', form=add_form)

@app.route('/find')
def new_movie():
    movie_id = request.args.get('id')
    if movie_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_id}"
        response = requests.get(url=movie_api_url, params={'api_key':MOVIE_DB_API_KEY})
        data = response.json()
        new_movie = Movie(
            title= data['title'],
            img_url = f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description= data['overview'],
            year = data['release_date'].split('-')[0],
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))

# movie_to_add= Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# db.session.add(movie_to_add)
# db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
