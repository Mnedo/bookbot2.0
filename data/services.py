import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm

class MasterRes(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'services'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    servicename = sqlalchemy.Column(sqlalchemy.String)
    duration = sqlalchemy.Column(sqlalchemy.Float, default=1.0)

    service_res = orm.relation("EventRes", back_populates='service')
