import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Feedback(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'feedbacks'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.user_id"))
    content = sqlalchemy.Column(sqlalchemy.String)

    user = orm.relation('UserRes')
