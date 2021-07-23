import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class UserRes(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, unique=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    surname = sqlalchemy.Column(sqlalchemy.String)
    user_name = sqlalchemy.Column(sqlalchemy.String)
    is_admin = sqlalchemy.Column(sqlalchemy.BOOLEAN, default=False)
    is_banned = sqlalchemy.Column(sqlalchemy.BOOLEAN, default=False)
    phone = sqlalchemy.Column(sqlalchemy.String)
    reg_time = sqlalchemy.Column(sqlalchemy.DateTime)
    events = sqlalchemy.Column(sqlalchemy.String) # id_1;id_2
    events_res = orm.relation("EventRes", back_populates='user')

