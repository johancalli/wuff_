from flask import Flask, jsonify, request, make_response, abort
from functools import wraps
from models import setup_db, db, Usuarios, Citas
from flask_cors import CORS
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import jwt
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
    
    @app.route('/citas', methods = ['GET','POST'])
    @token_required
    def crear_cita(current_user):
        if request.method == 'POST':
            response_object={'success':'','message':''}
            
            post_data = request.get_json()
            
            fecha = post_data.get('fecha')
            hora = post_data.get('hora')
            paseador = post_data.get('paseador')
            distrito = post_data.get('distrito')
            direccion = post_data.get('direccion')
            metodo_pago = post_data.get('pago')
            #revisar si existe conflicto de citas
            conflicto = db.session.query(Citas.id).filter_by(fecha=fecha,paseador=paseador,hora=hora).first() is not None

            if conflicto == True:
                response_object['success'] = False
                response_object['message'] = 'Ya existe una cita para este tiempo con este paseador'

                return jsonify(response_object)
                
            elif conflicto == False:
                response_object['success'] = True
                response_object['message'] = '¡Cita Programada!'

                data = Citas(fecha,hora,paseador,distrito,direccion,metodo_pago,current_user.id)

                db.session.add(data)
                db.session.commit()

                return jsonify(response_object)

        elif request.method== 'GET':
            citas_schema = CitasSchema(many=True)
            list = current_user.citas
            output = citas_schema.dump(list)
            return jsonify({'success':True,'citas':output})

    @app.route('/citas/<cita_id>', methods = ['PUT'])
    @token_required
    def update_cita(current_user,cita_id):
        response_object = {'success':'', 'message':''}
        post_data = request.get_json()

        fecha = post_data.get('fecha')
        hora = post_data.get('hora')
        paseador = post_data.get('paseador')
        distrito = post_data.get('distrito')
        direccion = post_data.get('direccion')
        metodo_pago = post_data.get('metodo_de_pago')

        conflicto = db.session.query(Citas).filter(Citas.id!=cita_id,Citas.fecha==fecha,
        Citas.paseador==paseador,Citas.hora==hora).first() is not None
    
        if conflicto == True:
            response_object['success'] = False
            response_object['message'] = 'Ya existe una cita para este tiempo con este paseador'
            return jsonify(response_object)
        else:
            response_object['success'] = True
            response_object['message'] = '¡Cita Remplazada!'

            cita = current_user.citas[cita_id] #acceder a la cita con su id
            
            cita.fecha = fecha
            cita.hora = hora
            cita.paseador = paseador
            cita.distrito = distrito
            cita.direccion = direccion
            cita.metodo_de_pago = metodo_pago

            db.session.commit()

            return jsonify(response_object)

    @app.route('/citas/<cita_id>', methods = ['DELETE'])
    @token_required
    def delete_cita(current_user,cita_id):

        response_object = {'success':True, 'message':'¡Cita eliminada!'}

        db.session.delete(current_user.citas[cita_id])
        db.session.commit()

        return jsonify(response_object)
    
    return app