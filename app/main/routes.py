from flask import render_template, request, redirect, url_for
from app.main import bp
from app.main.forms import SearchForm
from app.models import Category, Tag, Post

@bp.app_context_processor
def inject_global_vars():
    """Inject search form, navigation categories, and popular tags into all templates."""
    search_form = SearchForm()
    nav_categories = Category.query.order_by(Category.name.asc()).limit(8).all()
    popular_tags = Tag.query.order_by(Tag.name.asc()).limit(12).all()
    return dict(
        search_form=search_form,
        nav_categories=nav_categories,
        popular_tags=popular_tags
    )

@bp.route('/about')
def about():
    """About page for the blogging platform."""
    stats = {
        'posts': Post.query.filter_by(is_published=True).count(),
        'categories': Category.query.count(),
        'tags': Tag.query.count()
    }
    return render_template('main/about.html', title='About Us', stats=stats)

@bp.route('/search')
def search():
    """Handle navbar search query submission."""
    q = request.args.get('q', '').strip()
    return redirect(url_for('blog.index', q=q))

@bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html', title='Access Denied'), 403

@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html', title='Page Not Found'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html', title='Server Error'), 500
