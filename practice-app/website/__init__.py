from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flasgger import Swagger
import requests


db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'cmpe'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

    swagger = Swagger(app)

    db.init_app(app)

    
    from .views import views
    from .api.auth import auth
    from .api.event import events
    from .api.badge import badges

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(events, url_prefix='/api/v1.0/events/')
    app.register_blueprint(badges, url_prefix='/api/v1.0/badges/')
    
    from .models import User, Event

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def get_sport_names():
    uri = 'https://www.thesportsdb.com/api/v1/json/1/all_sports.php'

    r = requests.get(uri)
    
    result = r.json()

    sports={}

    for sport in result['sports']:
        sports[sport['idSport']] = sport['strSport']
    return sports

def create_database(app):
    if not path.exists('../website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')
        sports = get_sport_names()
        from .models import Sport
        with app.app_context():
            for sport in sports.keys():
                new_sport = Sport(
                    id = sport,
                    sport =  sports[sport]
                )
                try:
                    db.session.add(new_sport)
                    db.session.commit()
                except:
                    #Already exists
                    pass

