"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, People, Favorite
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/users', methods=['GET'])
def get_all_users():

    user_list = User.query.all()

    serialized_users = [ item.serialize() for item in user_list ]

    return jsonify(serialized_users), 200

# /////

@app.route('/planet', methods=['GET'])
def get_all_planets():

    planet_list = Planet.query.all()

    serialized_planets = [item.serialize() for item in planet_list]

    return jsonify(serialized_planets), 200


@app.route('/planet/<int:id>', methods=['GET'])
def get_one_planet(id):
    searched_planet = Planet.query.get(id)
    if searched_planet != None:
            return jsonify(searched_planet.serialize()), 200
    return jsonify({"error": "Planet no encontrado"}), 404


@app.route('/people', methods=['GET'])
def get_all_people():
    people_list = People.query.order_by(People.name.asc()).all()
    serialized_people = [item.serialize()for item in people_list]
    return jsonify(serialized_people), 200


@app.route('/people/<int:id>', methods=['GET'])
def get_one_people(id):
    searched_people = People.query.get(id)
    if searched_people != None:
            return jsonify(searched_people.serialize()), 200
    return jsonify({"error": "Planet no encontrado"}), 404


@app.route('/favorite', methods=['GET'])
def get_all_fav():
    fav_list =Favorite.query.order_by(Favorite.user_id.asc()).all()
    serialized_fav = [item.serialize()for item in fav_list]
    return jsonify(serialized_fav), 200


@app.route('/users/favorite/<int:user_id>', methods=['GET'])
def get_user_fav(user_id):
    searched_fav = Favorite.query.get(user_id)
    if searched_fav != None:
            return jsonify(searched_fav.serialize()), 200
    return jsonify({"error": "Favorites no encontrado"}), 404



@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    try:
        body = request.json
        user_id = body.get('user_id')

        if not user_id or not planet_id:
            return jsonify({"error": "Both 'user_id' and 'planet_id' are required."}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found."}), 404

        planet = Planet.query.get(planet_id)
        if not planet:
            return jsonify({"error": "Planet not found."}), 404

        existing_favorite = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
        if existing_favorite:
            return jsonify({"error": "This planet is already a favorite."}), 400

        new_favorite = Favorite(user_id=user_id, planet_id=planet_id)

        db.session.add(new_favorite)
        db.session.commit()

        return jsonify(new_favorite.serialize()), 201

    except ValueError as e:
        return jsonify({"error": f"Invalid JSON data: {str(e)}"}), 400
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 500   


@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    try:
        body = request.json
        user_id = body.get('user_id')

        if not user_id or not people_id:
            return jsonify({"error": "Both 'user_id' and 'people_id' are required."}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found."}), 404

        people = People.query.get(people_id)
        if not people:
            return jsonify({"error": "Person not found."}), 404

        existing_favorite = Favorite.query.filter_by(user_id=user_id, people_id=people_id).first()
        if existing_favorite:
            return jsonify({"error": "This person is already a favorite."}), 400

        new_favorite = Favorite(user_id=user_id, people_id=people_id)

        db.session.add(new_favorite)
        db.session.commit()

        return jsonify(new_favorite.serialize()), 201

    except ValueError as e:
        return jsonify({"error": f"Invalid JSON data: {str(e)}"}), 400
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 500


@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def remove_favorite_planet(planet_id):
    try:
        body = request.json
        user_id = body.get('user_id')

        if not user_id:
            return jsonify({"error": "The 'user_id' field is required."}), 400

        favorite = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()

        if favorite is None:
            return jsonify({ 
                "error": f"The favorite planet with id {planet_id} for user {user_id} was not found."
            }), 404

        db.session.delete(favorite)
        db.session.commit()

        return jsonify({"msg": "Favorite planet removed successfully"}), 200

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 500


@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def remove_favorite_people(people_id):
    try:
        body = request.json
        user_id = body.get('user_id')

        if not user_id:
            return jsonify({"error": "The 'user_id' field is required."}), 400

        favorite = Favorite.query.filter_by(user_id=user_id, people_id=people_id).first()

        if favorite is None:
            return jsonify({ 
                "error": f"The favorite person with id {people_id} for user {user_id} was not found."
            }), 404

        db.session.delete(favorite)
        db.session.commit()

        return jsonify({"msg": "Favorite person removed successfully"}), 200

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 500


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
