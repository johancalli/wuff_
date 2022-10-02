from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()

database_path = 'mysql://root:@localhost:3306/wuff'

def setup_db(app,database_path):
    app.config['SQLALCHEMY_DATABASE_URI']= database_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
    db.app = app
    db.init_app(app)
    db.create_all()

class Usuarios(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(200))
    nombre = db.Column(db.String(60))
    apellido = db.Column(db.String(60))
    username = db.Column(db.String(60))
    password_hash = db.Column(db.String(128))
    citas = db.relationship('Citas',backref='usuario') #relacion con tabla citas

    def verify_password(self,password):
        return check_password_hash(self.password_hash, password)

    #constructor
    def __init__(self,nombre,apellido,username,password):
        self.public_id = str(uuid.uuid4())
        self.nombre = nombre
        self.apellido = apellido
        self.username = username
        self.password_hash = generate_password_hash(password,method='sha256')


class Citas(db.Model):

    __tablename__ = 'citas_programadas'

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(200))
    hora = db.Column(db.String(200))
    paseador = db.Column(db.String(200))
    distrito = db.Column(db.String(200))
    direccion = db.Column(db.String(200))
    metodo_de_pago = db.Column(db.String(200))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id')) #foreign key a miembros (one to many)

    #constructor
    def __init__(self,fecha,hora,paseador,distrito,direccion,metodo_de_pago,usuario_id):
        self.fecha = fecha
        self.hora = hora
        self.paseador = paseador
        self.distrito = distrito
        self.direccion = direccion
        self.metodo_de_pago = metodo_de_pago
        self.usuario_id = usuario_id
