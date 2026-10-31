import os
from flask import Flask
from config import config
from app.extensions import db, migrate, login_manager, csrf

def create_app(config_name=None):
    """Application factory pattern for the Blogging Platform."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.blog import bp as blog_bp
    app.register_blueprint(blog_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Shell context for flask shell
    @app.shell_context_processor
    def make_shell_context():
        from app.models import User, Post, Category, Tag, Comment
        return {
            'db': db,
            'User': User,
            'Post': Post,
            'Category': Category,
            'Tag': Tag,
            'Comment': Comment
        }

    return app
