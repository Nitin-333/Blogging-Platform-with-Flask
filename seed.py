import os
from app import create_app
from app.extensions import db
from app.models import User, Post, Category, Tag, Comment

app = create_app(os.environ.get('FLASK_CONFIG', 'development'))

def seed_database():
    with app.app_context():
        print("[*] Seeding database with initial data...")
        db.create_all()

        # 1. Create Users
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@chronicle.local',
                bio='Platform Administrator and Editor-in-Chief. Managing publication quality and developer guidelines.',
                is_admin=True
            )
            admin.set_password('AdminPass123!')
            db.session.add(admin)

        alex = User.query.filter_by(username='alex_dev').first()
        if not alex:
            alex = User(
                username='alex_dev',
                email='alex@chronicle.local',
                bio='Senior Backend Engineer with a penchant for clean code, Python design patterns, and distributed systems.'
            )
            alex.set_password('Password123!')
            db.session.add(alex)

        sarah = User.query.filter_by(username='sarah_cloud').first()
        if not sarah:
            sarah = User(
                username='sarah_cloud',
                email='sarah@chronicle.local',
                bio='Cloud Architect & DevOps advocate. Writing about Kubernetes, Docker containerization, and resilient infra.'
            )
            sarah.set_password('Password123!')
            db.session.add(sarah)

        db.session.commit()
        print("[OK] Users verified.")

        # 2. Create Categories
        categories_data = [
            ("Flask & Python", "flask-python", "Deep dives into Python programming, Flask extensions, patterns, and libraries."),
            ("Software Architecture", "software-architecture", "Patterns, modular design, clean code principles, and domain logic."),
            ("Cloud & DevOps", "cloud-devops", "Containerization with Docker, CI/CD pipelines, orchestration, and infrastructure."),
            ("Web Development", "web-development", "Modern frontend frameworks, API contracts, UX design, and web security.")
        ]
        cat_map = {}
        for name, slug, desc in categories_data:
            cat = Category.query.filter_by(slug=slug).first()
            if not cat:
                cat = Category(name=name, slug=slug, description=desc)
                db.session.add(cat)
                db.session.flush()
            cat_map[slug] = cat
        db.session.commit()
        print("[OK] Categories verified.")

        # 3. Create Tags
        tags_data = ["python", "flask", "docker", "sqlalchemy", "architecture", "security", "devops", "beginners", "performance", "tutorial"]
        tag_map = {}
        for tag_name in tags_data:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
                db.session.flush()
            tag_map[tag_name] = tag
        db.session.commit()
        print("[OK] Tags verified.")

        # 4. Create Sample Posts
        posts_data = [
            {
                "title": "Mastering the Application Factory Pattern in Flask",
                "slug": "mastering-the-application-factory-pattern-in-flask",
                "summary": "Discover why the application factory pattern is essential for scalable Flask applications, automated testing, and multi-environment setups.",
                "category": cat_map["flask-python"],
                "author": alex,
                "tags": [tag_map["flask"], tag_map["python"], tag_map["architecture"]],
                "views": 142,
                "content": """
# Why Use the Application Factory Pattern?

When building microservices or web platforms with **Flask**, the simplest approach of instantiating `app = Flask(__name__)` globally often leads to circular import bottlenecks and rigid test configurations.

The **Application Factory Pattern** encapsulates the creation of your Flask app inside a function—typically named `create_app()`:

```python
def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.blog import bp as blog_bp
    app.register_blueprint(blog_bp)

    return app
```

## Key Advantages

1. **Multiple Instances for Testing**: Easily spin up isolated in-memory instances with custom configuration during unit test runs.
2. **Circular Import Elimination**: Extensions like `SQLAlchemy` and `LoginManager` are declared outside and attached later via `.init_app()`.
3. **Flexible Configurations**: Seamlessly switch between `DevelopmentConfig`, `TestingConfig`, and `ProductionConfig` using environment variables.

> "Structure your application for change from day one, and maintenance becomes effortless."
"""
            },
            {
                "title": "Containerizing Flask Apps with Docker and Gunicorn",
                "slug": "containerizing-flask-apps-with-docker-and-gunicorn",
                "summary": "A step-by-step production guide to packaging Python Flask applications inside slim Docker containers with Gunicorn and security best practices.",
                "category": cat_map["cloud-devops"],
                "author": sarah,
                "tags": [tag_map["docker"], tag_map["flask"], tag_map["devops"]],
                "views": 89,
                "content": """
# Production-Ready Docker Containers for Flask

Deploying a development server using `flask run` in production is insecure and unperformant. Instead, we bundle the app using **Gunicorn** inside an Alpine or Debian-slim container.

## The Dockerfile Blueprint

Here is an optimized multi-stage or lean single-stage Dockerfile:

```dockerfile
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as non-privileged user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
```

## Gunicorn Configuration Highlights

- Configure `workers = (2 * CPU_CORES) + 1` for synchronous I/O.
- Use `accesslog = "-"` to stream logs cleanly to container stdout.
- Ensure timeout thresholds protect against zombie connections.
"""
            },
            {
                "title": "Bulletproof Authentication and Session Protection in Flask",
                "slug": "bulletproof-authentication-and-session-protection-in-flask",
                "summary": "Safeguarding user accounts with Flask-Login, Werkzeug password hashing, CSRF tokens, and open-redirect defenses.",
                "category": cat_map["software-architecture"],
                "author": admin,
                "tags": [tag_map["security"], tag_map["flask"], tag_map["python"]],
                "views": 210,
                "content": """
# Hardening Web Application Security

Modern web security requires defense in depth. When implementing user authentication:

### 1. Robust Password Hashing
Never store plaintext or simple MD5 passwords. Werkzeug uses modern `scrypt` or `pbkdf2:sha256`:

```python
from werkzeug.security import generate_password_hash, check_password_hash

user.password_hash = generate_password_hash(password)
assert check_password_hash(user.password_hash, password)
```

### 2. Preventing Open Redirects
When handling the `?next=` query parameter upon login, always parse and validate the host:

```python
from urllib.parse import urlsplit

def is_safe_redirect_url(target):
    ref_url = urlsplit(request.host_url)
    test_url = urlsplit(target)
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc or not test_url.netloc
```

### 3. CSRF Protection
Enforce `Flask-WTF` CSRF token verification across all state-mutating requests (`POST`, `PUT`, `DELETE`).
"""
            },
            {
                "title": "Optimizing SQLAlchemy Queries and Avoiding N+1 Pitfalls",
                "slug": "optimizing-sqlalchemy-queries-and-avoiding-n-plus-1-pitfalls",
                "summary": "Learn how eager loading, subquery joins, and indexed database fields can dramatically accelerate response times.",
                "category": cat_map["flask-python"],
                "author": alex,
                "tags": [tag_map["sqlalchemy"], tag_map["performance"], tag_map["python"]],
                "views": 75,
                "content": """
# Eliminating the N+1 Query Problem

When rendering a list of blog posts alongside their categories and tags, a naive query triggers extra database queries for every individual item.

## Using Eager Loading
SQLAlchemy provides `joinedload` and `subqueryload` options to fetch related records in a single query:

```python
from sqlalchemy.orm import joinedload

posts = Post.query.options(joinedload(Post.tags), joinedload(Post.category)).all()
```

## Adding Strategic Indexes
Index columns that appear frequently in `WHERE`, `ORDER BY`, or `JOIN` conditions:
- `slug`: lookups by unique URL slug
- `created_at`: reverse chronological post feeds
- `is_published`: filtering active posts
"""
            }
        ]

        created_posts = []
        for pdata in posts_data:
            post = Post.query.filter_by(slug=pdata["slug"]).first()
            if not post:
                post = Post(
                    title=pdata["title"],
                    slug=pdata["slug"],
                    summary=pdata["summary"],
                    content=pdata["content"].strip(),
                    author_id=pdata["author"].id,
                    category_id=pdata["category"].id,
                    is_published=True,
                    views=pdata["views"]
                )
                post.render_content()
                post.tags = pdata["tags"]
                db.session.add(post)
                db.session.flush()
            created_posts.append(post)

        db.session.commit()
        print("[OK] Sample posts created.")

        # 5. Add Comments
        if created_posts:
            first_post = created_posts[0]
            if first_post.comments.count() == 0:
                c1 = Comment(
                    content="Outstanding explanation! The factory pattern completely cleaned up our circular import issues.",
                    post_id=first_post.id,
                    author_id=sarah.id
                )
                c2 = Comment(
                    content="Agreed. It also makes spinning up unit tests with an in-memory SQLite database a breeze.",
                    post_id=first_post.id,
                    author_id=admin.id
                )
                db.session.add_all([c1, c2])
                db.session.commit()
                print("[OK] Sample comments added.")

        print("[SUCCESS] Database successfully seeded!")
        print("Demo Credentials:")
        print("  - Admin: admin / AdminPass123!")
        print("  - User 1: alex_dev / Password123!")
        print("  - User 2: sarah_cloud / Password123!")

if __name__ == '__main__':
    seed_database()
