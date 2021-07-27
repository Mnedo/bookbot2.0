import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class MasterRes(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'masters'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True)
    mastername = sqlalchemy.Column(sqlalchemy.String)
    calendarId = sqlalchemy.Column(sqlalchemy.String)
    duration = sqlalchemy.Column(sqlalchemy.Float, default=1.0)
    services = sqlalchemy.Column(sqlalchemy.String)  # id1;id2

    master_res = orm.relation("EventRes", back_populates='master')
