import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class ServiceRes(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'services'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    servicename = sqlalchemy.Column(sqlalchemy.String)
    duration = sqlalchemy.Column(sqlalchemy.Float, default=1.0)
    master_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("masters.id"))

    service_res = orm.relation("EventRes", back_populates='service')
    master = orm.relation('MasterRes')