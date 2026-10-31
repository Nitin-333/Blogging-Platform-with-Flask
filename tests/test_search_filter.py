from app.extensions import db
from app.models import Post, Category, Tag

def test_search_by_title(client, test_post):
    """Test searching posts by title."""
    response = client.get('/?q=Intro+to+Flask')
    assert response.status_code == 200
    assert b'Intro to Flask Framework' in response.data
    assert b'Active filter:' in response.data

def test_search_by_content(client, test_post):
    """Test searching posts by body content keyword."""
    response = client.get('/?q=lightweight')
    assert response.status_code == 200
    assert b'Intro to Flask Framework' in response.data

def test_search_no_match(client, test_post):
    """Test searching for non-matching term."""
    response = client.get('/?q=NonExistentKeywordXYZ')
    assert response.status_code == 200
    assert b'No articles found' in response.data

def test_filter_by_category(client, test_post, test_category):
    """Test filtering posts by category slug."""
    response = client.get(f'/category/{test_category.slug}')
    assert response.status_code == 200
    assert test_post.title.encode() in response.data
    assert test_category.name.encode() in response.data

def test_filter_by_tag(client, test_post, test_tag):
    """Test filtering posts by tag slug."""
    response = client.get(f'/tag/{test_tag.slug}')
    assert response.status_code == 200
    assert test_post.title.encode() in response.data
    assert test_tag.name.encode() in response.data

def test_pagination(client, app, test_user, test_category):
    """Test pagination across multiple articles."""
    with app.app_context():
        # Create 5 extra posts
        for i in range(1, 6):
            p = Post(
                title=f'Pagination Article {i}',
                content=f'Body content for article {i}',
                author_id=test_user.id,
                category_id=test_category.id,
                is_published=True
            )
            p.render_content()
            db.session.add(p)
        db.session.commit()

    # In TestingConfig, POSTS_PER_PAGE = 3
    # First page should contain page links
    res_page1 = client.get('/?page=1')
    assert res_page1.status_code == 200
    assert b'Next &raquo;' in res_page1.data

    # Page 2
    res_page2 = client.get('/?page=2')
    assert res_page2.status_code == 200
    assert b'&laquo; Previous' in res_page2.data
