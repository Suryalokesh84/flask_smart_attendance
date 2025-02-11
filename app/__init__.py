from flask import Flask

def create_app():
    app = Flask(__name__)

    # Set the secret key to a random value
    app.config['SECRET_KEY'] = 'bhai'

    from .routes import main
    app.register_blueprint(main)

    return app
