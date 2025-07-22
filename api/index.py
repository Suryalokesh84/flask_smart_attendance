from app import create_app
def handler(environ, start_response):
    app = create_app()
    return app.wsgi_app(environ, start_response)