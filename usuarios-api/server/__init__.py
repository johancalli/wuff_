from flask import Flask, jsonify, request, make_response, abort
from werkzeug.security import generate_password_hash
from functools import wraps
from models import setup_db, db, Usuarios, Citas
from flask_cors import CORS
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import jwt
import datetime
import secrets

def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY']= '29ea5266607741e1532be5ba1e7463db'

    setup_db(app,'mysql://root:@localhost:3306/wuff')

    CORS(app, resources={r"/*":{"origins":"*"}})

    class UsuariosSchema(SQLAlchemyAutoSchema):
        class Meta:
            model = Usuarios
    
    class CitasSchema(SQLAlchemyAutoSchema):
        class Meta:
            model = Citas
    
    @app.errorhandler(404)
    def error404(_error):
        return make_response(jsonify({'error':'recurso no encontrado'}),404)
    
    @app.errorhandler(400)
    def error404(_error):
        return make_response(jsonify({'error':'Bad request'}),400)
    
    @app.errorhandler(500)
    def error500(_error):
        return make_response(jsonify({'error':'error interno del servidor'}),500)

    def token_required(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            token = None
            if 'x-access-tokens' in request.headers:
                token = request.headers['x-access-tokens']

            if not token:
                return jsonify({'message': 'falta un token valido'})
            try:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
                current_user = Usuarios.query.filter_by(public_id=data['public_id']).first()
            except:
                return jsonify({'message': 'token invalido'})
        
            return f(current_user, *args, **kwargs)
        
        return decorator
    
    @app.route('/signup',methods=['POST'])
    def signup():
        response_object = {'success':'','flag':'','message':''}
        data = request.get_json()
        name = data.get('name')
        last_name = data.get('apellido')
        user = data.get('user')
        password = data.get('password')

        #caracteres minimos para usuario y contraseña
        if len(user)<6:
            response_object['success'] = False
            response_object['flag'] = 'badUserLength'
            response_object['message'] = 'Usuario tiene que tener al menos 6 caracteres'
            return (jsonify(response_object))
        elif len(password)<8:
            response_object['success'] = False
            response_object['flag'] = 'badPassLength'
            response_object['message'] = 'Contraseña tiene que tener 8 caracteres'
            return (jsonify(response_object))
        
        #verificar si existe el usuario insertado
        exists_user = db.session.query(Usuarios.id).filter_by(username=user).first() is not None

        if exists_user == True:
            response_object['success'] = False
            response_object['flag'] ='exists_user'
            response_object['message'] = 'Usuario ya existente'
            return (jsonify(response_object))

        elif exists_user == False:
            #añadir nuevo usuario a base de datos
            response_object['success'] = True
            response_object['flag'] = 'green'
            response_object['message'] = 'Usuario registrado'
            data = Usuarios(name,last_name,user,password)
            db.session.add(data)
            db.session.commit()
            return (jsonify(response_object))

    @app.route('/login',methods=['POST'])
    def login():
        response_object={'success':'','flag':'','message':''}
        data = request.get_json()
        user = data.get('user')
        password = data.get('password')

        #verificamos si existe usuario
        exists_user = db.session.query(Usuarios.id).filter_by(username=user).first() is not None

        if exists_user == False:

            response_object['success'] = False
            response_object['flag'] ='notExists'
            response_object['message'] = 'Usuario no existe'

            return (jsonify(response_object))
        else:
            #ya se filtro la existencia del usuario entonces lo que queda verificar es contraseña con match
            usuario = Usuarios.query.filter_by(username=user).first()
            match = usuario.verify_password(password) #usamos metodo de verificacion

            if match == False:

                response_object['success'] = False
                response_object['flag'] ='badMatch'
                response_object['message'] = 'Contraseña incorrecta'

                return (jsonify(response_object))

            elif match == True:

                token = jwt.encode({'public_id' : usuario.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=45)},app.config['SECRET_KEY'], "HS256")

                response_object['success'] = True
                response_object['flag'] ='match'
                response_object['message'] = 'Usuario logueado'
                response_object['token'] = token
                
                return (jsonify(response_object))
            

    @app.route('/usuarios',methods=['GET'])
    @token_required
    def get_usuarios(current_user):
        usuarios_schema = UsuariosSchema(many=True)

        list = Usuarios.query.all()
        output = usuarios_schema.dump(list)

        return jsonify({'success':True,'usuarios':output})

    @app.route('/usuarios', methods = ['PUT'])
    @token_required
    def update_usuario(current_user):
        response_object = {'success':'', 'message':''}
        post_data = request.get_json()

        nombre = post_data.get('name')
        apellido = post_data.get('apellido')
        username = post_data.get('user')
        password = post_data.get('password')

        if len(username)<6:
            response_object['success'] = False
            response_object['flag'] = 'badUserLength'
            response_object['message'] = 'Usuario tiene que tener al menos 6 caracteres'
            return (jsonify(response_object))
        elif len(password)<8:
            response_object['success'] = False
            response_object['flag'] = 'badPassLength'
            response_object['message'] = 'Contraseña tiene que tener 8 caracteres'
            return (jsonify(response_object))

        conflicto = db.session.query(Usuarios).filter(Usuarios.username==username).first() is not None
    
        if conflicto == True:
            response_object['success'] = False
            response_object['message'] = 'Ya existe una un usuario con ese nombre'
            return jsonify(response_object)
        else:
            response_object['success'] = True
            response_object['message'] = '¡Datos actualizados!'

            current_user.nombre = nombre
            current_user.apellido = apellido
            current_user.username = username
            current_user.password_hash = generate_password_hash(password,method='sha256')

            db.session.commit()

            return jsonify(response_object)

    @app.route('/usuarios',methods=['DELETE'])
    @token_required    
    def delete_user(current_user):
        response_object = {'success':'','flag':'','message':''}
        response_object = {'success':True, 'message':'¡Usuario Eliminado!'}

        db.session.delete(current_user)
        db.session.commit()

        return jsonify(response_object)
    
    return app
    