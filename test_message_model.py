"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test models for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.user_id = 12345
        user = User.signup("a", "a@b.com", "test12", None)
        user.id = self.user_id
        db.session.commit()

        self.user = User.query.get(self.user_id)

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Testing warbles"""
        
        message = Message(
            text="test",
            user_id=self.user_id
        )

        db.session.add(message)
        db.session.commit()

        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, "test")

    def test_message_likes(self):
        """Testing liking a warble"""
        message1 = Message(
            text="test1",
            user_id=self.user_id
        )

        user = User.signup("ab", "b@c.com", "test34", None)
        user_id = 1234
        user.id = user_id
        db.session.add_all([message1, user])
        db.session.commit()

        user.likes.append(message1)

        db.session.commit()
        
        likes = Likes.query.filter(Likes.user_id == user_id).all()
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].message_id, message1.id)