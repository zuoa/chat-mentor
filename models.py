import datetime
import secrets
import string

import config
from peewee import (
    Model, SqliteDatabase, CharField, TextField,
    DateTimeField, PrimaryKeyField
)

# Connect to SQLite database
db = SqliteDatabase(config.DB_PATH)


class BaseModel(Model):
    class Meta:
        database = db


class Chat(BaseModel):
    id = CharField(primary_key=True, max_length=16)
    my_name = CharField(max_length=50, null=True)
    my_avatar = CharField(max_length=255, null=True)
    my_personality = TextField(null=True)

    other_name = CharField(max_length=50, null=True)
    other_avatar = CharField(max_length=50, null=True)
    other_personality = TextField(null=True)

    relationship = CharField(max_length=200, null=True)
    communication_history = TextField(null=True)
    objective = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

    @staticmethod
    def generate_short_id(length=8):
        """Generate a short, unique ID"""
        # Use a mix of lowercase letters and numbers for readability
        alphabet = string.ascii_lowercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @classmethod
    def create_chat(cls, chat_data):
        """Create a new HTML snippet"""
        # Generate a unique short ID
        while True:
            short_id = cls.generate_short_id()
            # Check if this ID already exists
            if not cls.select().where(cls.id == short_id).exists():
                break

        chat_data = {k: v for k, v in chat_data.items() if v is not None}
        chat_data['id'] = short_id
        chat_data['created_at'] = datetime.datetime.now()
        return cls.create(**chat_data)

    @classmethod
    def get_by_id_str(cls, id_str):
        """Get snippet by string ID"""
        try:
            return cls.get(cls.id == id_str)
        except cls.DoesNotExist:
            return None


class Message(BaseModel):
    """Model for storing messages in a chat"""
    id = PrimaryKeyField()
    chat_id = CharField(max_length=16)  # Reference to Chat ID
    sender = CharField(max_length=50)  # Name of the sender
    content = TextField()  # Message content
    created_at = DateTimeField(default=datetime.datetime.now)

    @classmethod
    def create_message(cls, chat_id, sender, content):
        return cls.create(
            chat_id=chat_id,
            sender=sender,
            content=content,
            created_at=datetime.datetime.now()
        )

def create_tables():
    """Create database tables if they don't exist"""
    with db:
        db.create_tables([Chat, Message])
