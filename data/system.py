import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class System(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'system'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    last_update = sqlalchemy.Column(sqlalchemy.DateTime)
    all_posts = sqlalchemy.Column(sqlalchemy.Integer)
    telegram_posts = sqlalchemy.Column(sqlalchemy.Integer)
    all_users = sqlalchemy.Column(sqlalchemy.Integer)
    timezone_int = sqlalchemy.Column(sqlalchemy.Integer)
    banned_users = sqlalchemy.Column(sqlalchemy.String)
    superusers = sqlalchemy.Column(sqlalchemy.String)
    title = sqlalchemy.Column(sqlalchemy.String)
    phone = sqlalchemy.Column(sqlalchemy.String)
    about = sqlalchemy.Column(sqlalchemy.VARCHAR)

