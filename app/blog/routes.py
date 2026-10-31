from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import current_user, login_required
from app.blog import bp
from app.blog.forms import PostForm, CommentForm
from app.extensions import db
from app.models import Post, Category, Tag, Comment, slugify

def populate_category_choices(form):
    """Helper to populate category choices for PostForm."""
    categories = Category.query.order_by(Category.name.asc()).all()
    form.category_id.choices = [(0, '-- None (Uncategorized) --')] + [
        (c.id, c.name) for c in categories
    ]

def process_tags(tag_string):
    """Parse comma-separated tag string into Tag models."""
    if not tag_string:
        return []
    names = [name.strip() for name in tag_string.split(',') if name.strip()]
    tags = []
    seen = set()
    for name in names:
        tag_slug = slugify(name)
        if tag_slug in seen:
            continue
        seen.add(tag_slug)
        tag = Tag.query.filter_by(slug=tag_slug).first()
        if not tag:
            tag = Tag(name=name, slug=tag_slug)
            db.session.add(tag)
        tags.append(tag)
    return tags

@bp.route('/')
def index():
    """Home feed listing blog posts with pagination, search, and category filters."""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '').strip()
    category_slug = request.args.get('category', '').strip()
    tag_slug = request.args.get('tag', '').strip()
    per_page = current_app.config.get('POSTS_PER_PAGE', 6)

    query = Post.query.filter_by(is_published=True)

    # Search filter
    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            (Post.title.ilike(search_filter)) |
            (Post.content.ilike(search_filter)) |
            (Post.summary.ilike(search_filter))
        )

    # Category filter
    selected_category = None
    if category_slug:
        selected_category = Category.query.filter_by(slug=category_slug).first()
        if selected_category:
            query = query.filter_by(category_id=selected_category.id)

    # Tag filter
    selected_tag = None
    if tag_slug:
        selected_tag = Tag.query.filter_by(slug=tag_slug).first()
        if selected_tag:
            query = query.filter(Post.tags.contains(selected_tag))

    pagination = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    posts = pagination.items

    categories = Category.query.order_by(Category.name.asc()).all()
    all_tags = Tag.query.order_by(Tag.name.asc()).all()

    return render_template(
        'blog/index.html',
        title='Home - Latest Articles',
        posts=posts,
        pagination=pagination,
        categories=categories,
        all_tags=all_tags,
        search_query=search_query,
        selected_category=selected_category,
        selected_tag=selected_tag
    )

@bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a new blog post."""
    form = PostForm()
    populate_category_choices(form)

    if form.validate_on_submit():
        category_id = form.category_id.data if form.category_id.data != 0 else None
        post = Post(
            title=form.title.data.strip(),
            summary=form.summary.data.strip() if form.summary.data else '',
            content=form.content.data,
            author_id=current_user.id,
            category_id=category_id,
            is_published=form.is_published.data
        )
        post.slug = Post.generate_unique_slug(post.title)
        post.render_content()
        post.tags = process_tags(form.tags.data)

        db.session.add(post)
        db.session.commit()
        flash('Your blog post has been created!', 'success')
        return redirect(url_for('blog.post_detail', slug=post.slug))

    return render_template('blog/post_form.html', title='Write New Article', form=form, is_edit=False)

@bp.route('/post/<slug>')
def post_detail(slug):
    """View an individual blog post and its comments."""
    post = Post.query.filter_by(slug=slug).first_or_404()

    # If post is unpublished draft, allow only author or admin to view
    if not post.is_published:
        if not (current_user.is_authenticated and (current_user.id == post.author_id or current_user.is_admin)):
            abort(404)

    # Increment views counter
    post.views += 1
    db.session.commit()

    comment_form = CommentForm()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('COMMENTS_PER_PAGE', 10)

    comments_pagination = post.comments.paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        'blog/post_detail.html',
        title=post.title,
        post=post,
        comments=comments_pagination.items,
        comments_pagination=comments_pagination,
        comment_form=comment_form
    )

@bp.route('/post/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(slug):
    """Edit an existing blog post."""
    post = Post.query.filter_by(slug=slug).first_or_404()

    if post.author_id != current_user.id and not current_user.is_admin:
        abort(403)

    form = PostForm()
    populate_category_choices(form)

    if form.validate_on_submit():
        post.title = form.title.data.strip()
        # Regenerate unique slug if title changed
        post.slug = Post.generate_unique_slug(post.title, post_id=post.id)
        post.summary = form.summary.data.strip() if form.summary.data else ''
        post.content = form.content.data
        post.render_content()
        post.category_id = form.category_id.data if form.category_id.data != 0 else None
        post.is_published = form.is_published.data
        post.tags = process_tags(form.tags.data)

        db.session.commit()
        flash('Your blog post has been updated.', 'success')
        return redirect(url_for('blog.post_detail', slug=post.slug))

    elif request.method == 'GET':
        form.title.data = post.title
        form.summary.data = post.summary
        form.category_id.data = post.category_id or 0
        form.content.data = post.content
        form.tags.data = post.tag_names_string()
        form.is_published.data = post.is_published

    return render_template(
        'blog/post_form.html',
        title=f"Edit - {post.title}",
        form=form,
        post=post,
        is_edit=True
    )

@bp.route('/post/<slug>/delete', methods=['POST'])
@login_required
def delete_post(slug):
    """Delete a blog post."""
    post = Post.query.filter_by(slug=slug).first_or_404()

    if post.author_id != current_user.id and not current_user.is_admin:
        abort(403)

    db.session.delete(post)
    db.session.commit()
    flash(f'Post "{post.title}" has been deleted.', 'info')
    return redirect(url_for('blog.index'))

@bp.route('/post/<slug>/comment', methods=['POST'])
@login_required
def add_comment(slug):
    """Add a new comment to a post."""
    post = Post.query.filter_by(slug=slug).first_or_404()
    form = CommentForm()

    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data.strip(),
            post_id=post.id,
            author_id=current_user.id
        )
        comment.render_content()
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')

    return redirect(url_for('blog.post_detail', slug=post.slug) + '#comments')

@bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """Delete a comment."""
    comment = db.get_or_404(Comment, comment_id)
    post_slug = comment.post.slug

    # Author of comment, author of post, or admin can delete
    if not (current_user.id == comment.author_id or current_user.id == comment.post.author_id or current_user.is_admin):
        abort(403)

    db.session.delete(comment)
    db.session.commit()
    flash('Comment has been removed.', 'info')
    return redirect(url_for('blog.post_detail', slug=post_slug) + '#comments')

@bp.route('/category/<slug>')
def category_posts(slug):
    """View posts for a specific category."""
    category = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 6)

    pagination = category.posts.filter_by(is_published=True).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'blog/category_tag.html',
        title=f"Category: {category.name}",
        filter_type='Category',
        filter_name=category.name,
        filter_description=category.description,
        posts=pagination.items,
        pagination=pagination
    )

@bp.route('/tag/<slug>')
def tag_posts(slug):
    """View posts associated with a specific tag."""
    tag = Tag.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 6)

    pagination = tag.posts.filter_by(is_published=True).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'blog/category_tag.html',
        title=f"Tag: #{tag.name}",
        filter_type='Tag',
        filter_name=f"#{tag.name}",
        filter_description=f"Articles tagged with #{tag.name}",
        posts=pagination.items,
        pagination=pagination
    )
