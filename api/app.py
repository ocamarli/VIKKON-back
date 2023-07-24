from datetime import timedelta
from flask import Flask, request
from flask import jsonify
from config import config
from flask_pymongo import PyMongo
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager, create_refresh_token
from flask_cors import CORS
from User import User, FullTemplate
from bson.objectid import ObjectId
from bson.json_util import dumps, loads
from bson import json_util

import json


def create_app(env):
    app = Flask(__name__)
    CORS(app)
    app.config['DEBUG'] = env.DEBUG
    app.config["MONGO_URI"] = env.MONGO_DATABASE_URI
    app.config["JWT_SECRET_KEY"] = env.API_JWT_SECRET
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=100)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    app.config.from_object(env)

    return app


env = config['local']
app = create_app(env)
jwt = JWTManager(app)
mongo = PyMongo(app)

# Register a callback function that takes whatever object is passed in as the
# identity when creating JWTs and converts it to a JSON serializable format.


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user


# Register a callback function that loads a user from your database whenever
# a protected route is accessed. This should return any python object on a
# successful lookup, or None if the lookup failed for any reason (for example
# if the user has been deleted from the database).
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    user_dict = json.loads(identity)
    user_id = user_dict['id']
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

    if user:
        return User(str(user['_id']), user["username"], user['role']).toJSON()
    else:
        return None


@app.route("/")
def root():
    return "Works!!"


@app.route('/api/v1/login', methods=['POST'])
def login():
    json = request.get_json()
    if json != None:
        username = json["username"]
        password = json["password"]
        if username == None or password == None:
            return jsonify({"msg": "Bad username or password"}), 401

        try:
            user = mongo.db.users.find_one(
                {"username": username, "password": password})
            if (user != None):
                print(str(user['_id']))
                ity = User(str(user['_id']), user["username"],
                           user["role"]).toJSON()
                access_token = create_access_token(identity=ity)
                refresh_token = create_refresh_token(identity=ity)
                return jsonify(access_token=access_token, refresh_token=refresh_token, msg="Access token granted", status=True), 200

            else:
                return jsonify(status=False, msg='User not found!'), 401
        except:
            return jsonify(status=False, msg="".join(['Error: couldnt retrieve info about [', str(username), ']'])), 500
    else:
        return jsonify(status=False, msg="Missing request parameters"), 400

# We are using the `refresh=True` options in jwt_required to only allow
# refresh tokens to access this route.


@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token)


@app.route("/api/v1/user", methods=['POST'])
@jwt_required()
def register():
    json = request.get_json()
    if json != None:
        try:
            username = json["username"]
            user_found = mongo.db.users.find_one({"username": username})

            if user_found:
                return jsonify(status=False, msg="User exists"), 400

            mongo.db.users.insert_one(json)
            return jsonify(status=True, msg="User " + str(username) + " added"), 200
        except:
            return jsonify(status=False, msg="Error: user not added"), 500
    else:
        return jsonify(status=False, msg="Missing request parameters"), 400


@app.route("/api/v1/fileTemplate/set", methods=['POST'])
@jwt_required()
def fileTemplate():
    json = request.get_json()
    if json != None:
        try:
            idTemplate=json["id_template"]
            text=json["text"]
            print(text)
            print(idTemplate)
            mongo.db.templates.update_one({"id_template": idTemplate}, {"$set": {"code": text}})

            return jsonify(status=True, msg="Text added"), 200
        except:
            return jsonify(status=False, msg="Error: Text added"), 500
    else:
        return jsonify(status=False, msg="Missing request text"), 400


@app.route('/api/v1/parameters/set', methods=['POST'])
@jwt_required()
def parameters():
    json = request.get_json()
    if json != None:
        try:
            mongo.db.parameters.insert_one(json)
            return jsonify(status=True, msg="Parameter added"), 200
        except:
            return jsonify(status=False, msg="Error: parameter not added"), 500
    else:
        return jsonify(status=False, msg="Missing request parameters"), 400


@app.route('/api/v1/recipe/set', methods=['POST'])
@jwt_required()
def receipe():
    json = request.get_json()
    if json != None:
        try:
            mongo.db.recipes.insert_one(json)
            return jsonify(status=True, msg="Receipe added"), 200
        except:
            return jsonify(status=False, msg="Error: Recipe not added"), 500
    else:
        return jsonify(status=False, msg="Missing request recipes"), 400


@app.route('/api/v1/templates/set', methods=['POST'])
@jwt_required()
def parametersTemplate():
    json = request.get_json()
    if json != None:
        try:
            mongo.db.templates.insert_one(json)
            return jsonify(status=True, msg="Template added"), 200
        except:
            return jsonify(status=False, msg="Error: Template not added"), 500
    else:
        return jsonify(status=False, msg="Missing request parameters"), 400


@app.route('/api/v1/parameters/set/list', methods=['POST'])
@jwt_required()
def parametersbylist():
    json = request.get_json()
    if json != None:
        try:
            mongo.db.parameters.insert_many(json)
            return jsonify(status=True, msg=str(len(json)) + " records added"), 200
        except:
            return jsonify(status=False, msg="Error: parameter list not added"), 500
    else:
        return jsonify(status=False, msg="Missing request parameters"), 400
    
@app.route('/api/v1/recipe/parameter/update', methods=['POST'])
@jwt_required()
def updateParameterRecipe():
    json = request.get_json()
    if json is not None:
        try:
            id_recipe=json["data"]["id_recipe"]
            id_parameter=json["data"]["id_parameter"]
            value=json["data"]["value"]
            result = mongo.db.recipes.update_one({'id_recipe': id_recipe, 'parameters.id_parameter': id_parameter},
                                                    {'$set': {'parameters.$.value': value}})
            if result.modified_count > 0:
                return jsonify(status=True, msg="Recipe parameter updated"), 200
            else:
                return jsonify(status=False, msg="Error: Recipe or parameter not found"), 404
        except:
            return jsonify(status=False, msg="Error: Recipe parameter not updated"), 500
    else:
        return jsonify(status=False, msg="Missing request body"), 400
@app.route('/api/v1/recipe/parameter/get', methods=['POST'])
@jwt_required()
def getParameterRecipe():
    json = request.get_json()
    if json is not None:
        try:
            id_recipe=json["data"]["id_recipe"]
            id_parameter=json["data"]["id_parameter"]
            print(id_parameter,id_recipe)
            result = mongo.db.recipes.find_one(
    {'id_recipe': id_recipe, 'parameters': {'$elemMatch': {'id_parameter': id_parameter}}},
    {'_id':False, 'parameters.$': True})
            if result is not None:

                return jsonify(status=True, msg="Recipe parameter ok", parameterRecipe=result['parameters'][0]), 200
            else:
                return jsonify(status=False, msg="Error: Recipe or parameter not found"), 404
        except:
            return jsonify(status=False, msg="Error: Recipe parameter"), 500
    else:
        return jsonify(status=False, msg="Missing request body"), 400    

@app.route("/api/v1/recipe/<string:id_recipe>", methods=["GET"])
def get_recipe(id_recipe):
    if id_recipe is not None:
        try:
           print("recipe",str(id_recipe))
           result = mongo.db.recipes.find_one({'id_recipe': str(id_recipe)}) 
           result['_id'] = str(result['_id'])
           result.pop('_id', None)

           result=dict(result)

           return jsonify(status=True, data=result), 200
        except:
            return jsonify(status=False, msg="Error: Recipe parameter"), 500
@app.route('/api/v1/parameters/get', methods=['GET'])
@jwt_required()
def get_parameters():
    parameters = []
    msg = ""
    status = False
    try:
        for parameter in mongo.db.parameters.find():
            print(parameter['description'])
            parameters.append({
                'name': parameter['name'],
                'description': parameter['description'],
                'id_parameter': parameter['id_parameter']
            })
        msg = "".join([str(len(parameters)), ' parameters in stack'])
        status = True
    except:
        msg = "Error: could not retireve parameters info"
        status = False

    code = 200 if status else 500
    return jsonify(parameters=parameters, msg=msg, status=status), code

@app.route('/api/v1/fileTemplate/get', methods=['POST'])
@jwt_required()
def get_fileTemplate():
    text = ""
    msg = ""
    status = False
    try:
        
        id_template = request.json['id_template']
        text = mongo.db.templates.find_one({"id_template": id_template})
        if text:
            text = text["code"]
            msg = "Code found"
            status = True
        else:
            msg = "Code not found"
            status = False
            text = ""
    except:
        msg = "Error: could not retrieve code info"
        status = False
        text = ""
    code = 200 if status else 500
    return jsonify(code=text, msg=msg, status=status), code


@app.route('/api/v1/recipes/get', methods=['GET'])
@jwt_required()
def get_recipes():
    recipes = []
    msg = ""
    status = False
    try:
        for recipe in mongo.db.recipes.find():
            recipes.append({
                'name': recipe['name'],
                'id_template': recipe['id_template'],
                'id_recipe': recipe['id_recipe'],
                'description': recipe['description'],
            })
        msg = "".join([str(len(recipes)), ' recipes in stack'])
        status = True
    except:
        msg = "Error: could not retireve recipes info"
        status = False

    code = 200 if status else 500
    return jsonify(recipes=recipes, msg=msg, status=status), code


@app.route('/api/v1/templates/get', methods=['GET'])
@jwt_required()
def get_templates():
    templates = []
    msg = ""
    status = False
    try:
        for template in mongo.db.templates.find():
            templates.append({
                'name': template['name'],
                'description': template['description'],
                'id_template': template['id_template'],
                'parameters': template['parameters'],
                'version': template['version'],
            })
        msg = "".join([str(len(templates)), ' templates in stack'])
        status = True
    except:
        msg = "Error: could not retireve templates info"
        status = False

    code = 200 if status else 500
    return jsonify(templates=templates, msg=msg, status=status), code


@app.route('/api/v1/fulltemplates/get', methods=['POST'])
@jwt_required()
def get_templates_id():
    templates = []
    msg = ""
    status = False
    json = request.get_json()
    if json != None:
        id_template = json['id_template']
        print(id_template)

        try:
            template = mongo.db.templates.find_one(
                {'id_template': id_template})
            if template:
                parameters = template['parameters']
                print(parameters)
                params = []
                for param in parameters:
                    p = mongo.db.parameters.find_one({'id_parameter': param})
                    # js = dumps(p,default=json_util.default)
                    params.append(p)

                template['parameters'] = params
                temp = dumps(template, default=json_util.default)

                msg = "".join(['template found'])
                status = True
                code = 200 if status else 500
                return jsonify(template=temp, msg=msg, status=status), code

        except:
            msg = "Error: could not retireve parameters info"
            status = False
            return jsonify(msg=msg, status=status), 500
    else:
        return jsonify(status=False, msg="Missing request parameters"), 400


if __name__ == '__main__':
    app.run()
