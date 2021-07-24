import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class NotifRes(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'notifications'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    context = sqlalchemy.Column(sqlalchemy.String)
    name = sqlalchemy.Column(sqlalchemy.String)
    trigger = sqlalchemy.Column(sqlalchemy.DateTime)
    system_id = sqlalchemy.Column(sqlalchemy.String)


