"""Message View tests."""

# run these tests like:
#
#    python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 8989
        self.testuser.id = self.testuser_id

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Session key to mimic logging in
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_no_user(self):
        """Testing adding a message without being logged in (should fail)"""
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
    
    def test_show_message(self):
        """Testing showing message details"""

        m = Message(
            id=1234,
            text="test",
            user_id=self.testuser_id
        )
        
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            m = Message.query.get(1234)

            resp = c.get(f'/messages/{m.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(m.text, str(resp.data))

    def test_show_invalid_message(self):
        """Test showing message details for message that doesn't exist (should 404)"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get('/messages/99999999')

            self.assertEqual(resp.status_code, 404)

    def test_message_delete(self):
        """Test deleting a message"""

        m = Message(
            id=1234,
            text="test",
            user_id=self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            m = Message.query.get(1234)
            self.assertIsNone(m)

    def test_unauthorized_message_delete(self):
        """Test a user that is not the message owner trying to delete message"""

        # A second user that will try to delete the message
        u = User.signup(username="unauthorized-user",
                        email="testtest@test.com",
                        password="password",
                        image_url=None)
        u.id = 12345

        #Message is owned by testuser
        m = Message(
            id=1234,
            text="test",
            user_id=self.testuser_id
        )
        db.session.add_all([u, m])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 12345

            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(1234)
            self.assertIsNotNone(m)

    def test_message_delete_no_authentication(self):
        """Test deleting a message without being logged in"""

        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(1234)
            self.assertIsNotNone(m)

