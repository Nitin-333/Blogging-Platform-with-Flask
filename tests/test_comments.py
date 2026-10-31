from app.extensions import db
from app.models import Comment

def test_add_comment_authenticated(client, auth, test_post, test_user, app):
    """Test authenticated user posting a comment."""
    auth.login()
    response = client.post(
        f'/post/{test_post.slug}/comment',
        data={'content': 'This was a really helpful tutorial, thank you!'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Your comment has been posted!' in response.data
    assert b'This was a really helpful tutorial, thank you!' in response.data

    with app.app_context():
        comment = Comment.query.filter_by(post_id=test_post.id).first()
        assert comment is not None
        assert comment.author_id == test_user.id
        assert 'really helpful' in comment.content

def test_add_comment_unauthenticated_redirects(client, test_post):
    """Test unauthenticated user cannot post a comment."""
    response = client.post(
        f'/post/{test_post.slug}/comment',
        data={'content': 'Anonymous comment.'}
    )
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']

def test_delete_comment_by_author(client, auth, test_post, test_user, app):
    """Test author deleting their own comment."""
    auth.login()
    # Add comment
    client.post(
        f'/post/{test_post.slug}/comment',
        data={'content': 'A comment to delete'},
        follow_redirects=True
    )

    with app.app_context():
        comment = Comment.query.filter_by(content='A comment to delete').first()
        comment_id = comment.id

    # Delete comment
    res = client.post(f'/comment/{comment_id}/delete', follow_redirects=True)
    assert res.status_code == 200
    assert b'Comment has been removed.' in res.data

    with app.app_context():
        assert db.session.get(Comment, comment_id) is None

def test_delete_comment_unauthorized_forbidden(client, auth, second_user, test_post, test_user, app):
    """Test unauthorized user cannot delete someone else's comment."""
    with app.app_context():
        comment = Comment(
            content='User 1 comment',
            post_id=test_post.id,
            author_id=test_user.id
        )
        db.session.add(comment)
        db.session.commit()
        comment_id = comment.id

    # Log in as Jane Doe
    auth.login(login_id='janedoe', password='Password123!')
    response = client.post(f'/comment/{comment_id}/delete')
    assert response.status_code == 403
