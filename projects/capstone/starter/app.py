import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from auth import AuthError, requires_auth
from models import db_drop_and_create_all, setup_db, Actor, Movie
from config import pagination

ROWS_PER_PAGE = pagination['page_limit']

def create_app(test_config=None):
  
  app = Flask(__name__)
  setup_db(app)
  db_drop_and_create_all()

  CORS(app)
  # CORS Headers 
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
      return response

  def get_error_message(error, default_text):
      try:
          return error.description['message']
      except:
          return default_text

  def paginate_results(request, selection):

    # Get page from request. If not given, default to 1
    page = request.args.get('page', 1, type=int)
    
    # Calculate start and end slicing
    start =  (page - 1) * ROWS_PER_PAGE
    end = start + ROWS_PER_PAGE

    # Format
    objects_formatted = [object_name.format() for object_name in selection]
    return objects_formatted[start:end]

  @app.route('/actors', methods=['GET'])
  @requires_auth('read:actors')
  def get_actors(payload):

    selection = Actor.query.all()
    actors_paginated = paginate_results(request, selection)

    if len(actors_paginated) == 0:
      abort(404, {'message': 'no actors found in database.'})

    return jsonify({
      'success': True,
      'actors': actors_paginated
    })

  @app.route('/actors', methods=['POST'])
  @requires_auth('create:actors')
  def insert_actors(payload):

    body = request.get_json()

    if not body:
          abort(400, {'message': 'request does not contain a valid JSON body.'})

    name = body.get('name')
    age = body.get('age')
    gender = body.get('gender')

    # abort if one of these are missing with appropiate error message
    if not name:
      abort(422, {'message': 'Name not provided.'})

    if not age:
      abort(422, {'message': 'Age not provided.'})

    if not gender:
      abort(422, {'message': 'Gender not provided.'})

    new_actor = (Actor(
          name = name, 
          age = age,
          gender = gender
          ))
    new_actor.insert()

    return jsonify({
      'success': True,
      'actor_id': new_actor.id
    })

  @app.route('/actors/<actor_id>', methods=['PATCH'])
  @requires_auth('edit:actors')
  def edit_actors(payload, actor_id):

    body = request.get_json()

    if not actor_id:
      abort(400, {'message': 'Actor id is not provided'})

    if not body:
      abort(400, {'message': 'No data provided'})

    actor_to_update = Actor.query.filter(Actor.id == actor_id).one_or_none()

    if not actor_to_update:
      abort(404, {'message': 'Actor with id {} not found in database.'.format(actor_id)})

    # Extract name and age value from request body
    # If not given, set existing field values, so no update will happen
    name = body.get('name', actor_to_update.name)
    age = body.get('age', actor_to_update.age)
    gender = body.get('gender', actor_to_update.gender)

    # Set new field values
    actor_to_update.name = name
    actor_to_update.age = age
    actor_to_update.gender = gender

    # Update
    actor_to_update.update()

    return jsonify({
      'success': True,
      'updated_actor_id': actor_to_update.id,
      'actor' : [actor_to_update.format()]
    })

  @app.route('/actors/<actor_id>', methods=['DELETE'])
  @requires_auth('delete:actors')
  def delete_actors(payload, actor_id):

    # no actor_id
    if not actor_id:
      abort(400, {'message': 'Actor to delete is not provided'})

    actor_to_delete = Actor.query.filter(Actor.id == actor_id).one_or_none()

    if not actor_to_delete:
        abort(404, {'message': 'Actor with id {} not found in database.'.format(actor_id)})
    
    # Delete
    actor_to_delete.delete()
    
    # Return success and id from deleted actor
    return jsonify({
      'success': True,
      'deleted_actor_id': actor_id
    })


  @app.route('/movies', methods=['GET'])
  @requires_auth('read:movies')
  def get_movies(payload):

    selection = Movie.query.all()
    movies_paginated = paginate_results(request, selection)

    if len(movies_paginated) == 0:
      abort(404, {'message': 'no movies found'})

    return jsonify({
      'success': True,
      'movies': movies_paginated
    })

  @app.route('/movies', methods=['POST'])
  @requires_auth('create:movies')
  def insert_movies(payload):

    body = request.get_json()

    if not body:
          abort(400, {'message': 'no details provided in body'})

    title = body.get('title')
    release_date = body.get('release_date')

    if not title:
      abort(422, {'message': 'title not provided.'})

    if not release_date:
      abort(422, {'message': 'Release_date not provided'})

    new_movie = (Movie(
          title = title, 
          release_date = release_date
          ))
    new_movie.insert()

    return jsonify({
      'success': True,
      'movie_id': new_movie.id
    })

  @app.route('/movies/<movie_id>', methods=['PATCH'])
  @requires_auth('edit:movies')
  def edit_movies(payload, movie_id):

    body = request.get_json()

    # no movie_id
    if not movie_id:
      abort(400, {'message': 'Movie id not provided'})

    if not body:
      abort(400, {'message': 'Update details not found'})

    movie_to_update = Movie.query.filter(Movie.id == movie_id).one_or_none()

    # no movie found
    if not movie_to_update:
      abort(404, {'message': 'Movie with id {} not found in database.'.format(movie_id)})

    title = body.get('title', movie_to_update.title)
    release_date = body.get('release_date', movie_to_update.release_date)

    # Set new field values
    movie_to_update.title = title
    movie_to_update.release_date = release_date

    movie_to_update.update()

    return jsonify({
      'success': True,
      'updated_movie_id': movie_to_update.id,
      'movie' : [movie_to_update.format()]
    })

  @app.route('/movies/<movie_id>', methods=['DELETE'])
  @requires_auth('delete:movies')
  def delete_movies(payload, movie_id):
    # no movie_id provided
    if not movie_id:
      abort(400, {'message': 'Movie id not provided'})

    movie_to_delete = Movie.query.filter(Movie.id == movie_id).one_or_none()

    # not found
    if not movie_to_delete:
        abort(404, {'message': 'Movie with id {} not found in database.'.format(movie_id)})
    
    # Delete
    movie_to_delete.delete()
    
    return jsonify({
      'success': True,
      'deleted_movie_id': movie_id
    })

  # Error Handlers

  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
                      "success": False, 
                      "error": 422,
                      "message": get_error_message(error,"unprocessable")
                      }), 422

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
                      "success": False, 
                      "error": 400,
                      "message": get_error_message(error, "bad request")
                      }), 400

  @app.errorhandler(404)
  def ressource_not_found(error):
      return jsonify({
                      "success": False, 
                      "error": 404,
                      "message": get_error_message(error, "resource not found")
                      }), 404

  @app.errorhandler(AuthError)
  def authentification_failed(AuthError): 
      return jsonify({
                      "success": False, 
                      "error": AuthError.status_code,
                      "message": AuthError.error['description']
                      }), AuthError.status_code
  return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)