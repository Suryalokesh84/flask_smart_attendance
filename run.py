from app import create_app

app = create_app()

# Import AFTER app creation
from app.admin_routes import admin
app.register_blueprint(admin, url_prefix='/admin')

if __name__ == '__main__':
    app.run(debug=True)
