"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()


class UserModelTestCase(TestCase):
    """Test models for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        u1 = User.signup("test1", "email1@email.com", "password", None)
        uid1 = 1111
        u1.id = uid1

        u2 = User.signup("test2", "email2@email.com", "password", None)
        uid2 = 2222
        u2.id = uid2

        db.session.commit()

        u1 = User.query.get(uid1)
        u2 = User.query.get(uid2)

        self.u1 = u1
        self.uid1 = uid1

        self.u2 = u2
        self.uid2 = uid2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
    
    def test_repr_method(self):
        """Testing repr method"""

        repr_test = self.u1.__repr__()
        self.assertEqual(repr_test, f"<User #{self.u1.id}: {self.u1.username}, {self.u1.email}>")

    def test_is_following(self):
        """Testing is_following method"""

        self.u1.following.append(self.u2)

        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        """Testing is_followed_by method"""

        self.u1.following.append(self.u2)

        db.session.commit()

        self.assertFalse(self.u1.is_followed_by(self.u2))
        self.assertTrue(self.u2.is_followed_by(self.u1))
    
    def test_user_create_invalid(self):
        """Testing creating an invalid user"""

        u = User.signup("test2", "email2@email.com", "password", None)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_user_authenticate(self):
        """Test authenticating a user"""

        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.uid1)

    def test_user_authenticate_username_invalid(self):
        """Test authenticating a user with an invalid username"""

        self.assertFalse(User.authenticate("dsaijgnaifd", "password"))

    def test_user_authenticate_password_invalid(self):
        """Test authenticating a user with an invalid password"""

        self.assertFalse(User.authenticate(self.u1.username, "asdfdasfwer"))