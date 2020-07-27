"""User View tests."""

# run these tests like:
#
#    python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 8989
        self.testuser.id = self.testuser_id

        self.u1 = User.signup("abc", "test1@test.com", "password", None)
        self.u1_id = 778
        self.u1.id = self.u1_id
        self.u2 = User.signup("efg", "test2@test.com", "password", None)
        self.u2_id = 884
        self.u2.id = self.u2_id
        self.u3 = User.signup("hij", "test3@test.com", "password", None)
        self.u4 = User.signup("testing", "test4@test.com", "password", None)

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_users_index(self):
        """Test being able to find all users"""
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@abc", str(resp.data))
            self.assertIn("@efg", str(resp.data))
            self.assertIn("@hij", str(resp.data))
            self.assertIn("@testing", str(resp.data))

    def test_users_search(self):
        """Test being able to search for certain users based on a query string"""
        with self.client as c:
            resp = c.get("/users?q=test")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@testing", str(resp.data))            

            self.assertNotIn("@abc", str(resp.data))
            self.assertNotIn("@efg", str(resp.data))
            self.assertNotIn("@hij", str(resp.data))

    def test_user_show(self):
        """Test being able to go to a user's profile"""
        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testuser", str(resp.data))

    def setup_likes(self):
        """Set up likes for testing"""
        m1 = Message(text="trending warble", user_id=self.testuser_id)
        m2 = Message(text="Eating some lunch", user_id=self.testuser_id)
        m3 = Message(id=9876, text="likable warble", user_id=self.u1_id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.testuser_id, message_id=9876)

        db.session.add(l1)
        db.session.commit()

    def test_user_show_with_likes(self):
        """Test showing likes on a user's profile"""
        self.setup_likes()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testuser", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            self.assertIn("2", found[0].text)

            self.assertIn("0", found[1].text)

            self.assertIn("0", found[2].text)

            self.assertIn("1", found[3].text)

    def test_add_like(self):
        """Test liking a post"""
        m = Message(id=1984, text="The earth is round", user_id=self.u1_id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post("/users/add_like/1984", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==1984).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)

    def test_remove_like(self):
        """Test unliking a post"""
        self.setup_likes()

        m = Message.query.filter(Message.text=="likable warble").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.testuser_id)

        l = Likes.query.filter(
            Likes.user_id==self.testuser_id and Likes.message_id==m.id
        ).one()

        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post(f"/users/add_like/{m.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            self.assertEqual(len(likes), 0)

    def test_unauthenticated_like(self):
        """Test liking a post while not logged in"""
        self.setup_likes()

        m = Message.query.filter(Message.text=="likable warble").one()
        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/users/add_like/{m.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))

            self.assertEqual(like_count, Likes.query.count())

    def setup_followers(self):
        """Set up followers for testing"""
        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()

    def test_user_show_with_follows(self):
        """Test showing a user's amount of followers and people followed"""

        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testuser", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            self.assertIn("0", found[0].text)

            self.assertIn("2", found[1].text)

            self.assertIn("1", found[2].text)

            self.assertIn("0", found[3].text)

    def test_show_following(self):
        """Test showing the people a user is following"""

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@abc", str(resp.data))
            self.assertIn("@efg", str(resp.data))
            self.assertNotIn("@hij", str(resp.data))
            self.assertNotIn("@testing", str(resp.data))

    def test_show_followers(self):
        """Test showing the people following a user"""

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/followers")

            self.assertIn("@abc", str(resp.data))
            self.assertNotIn("@efg", str(resp.data))
            self.assertNotIn("@hij", str(resp.data))
            self.assertNotIn("@testing", str(resp.data))

    def test_unauthorized_following_page_access(self):
        """Test trying to access the following page while not logged in"""
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@abc", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_followers_page_access(self):
        """Test trying to access the followers page while not logged in"""
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@abc", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))