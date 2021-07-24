import sqlalchemy
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class EventRes(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'events'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    master_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("masters.id"))
    service_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("services.id"))
    has_notified = sqlalchemy.Column(sqlalchemy.BOOLEAN, default=False)
    reg_time = sqlalchemy.Column(sqlalchemy.DateTime)
    start_time = sqlalchemy.Column(sqlalchemy.DateTime)
    end_time = sqlalchemy.Column(sqlalchemy.DateTime)
    event_id = sqlalchemy.Column(sqlalchemy.String)
    user = orm.relation('UserRes')
    master = orm.relation('MasterRes')
    service = orm.relation('ServiceRes')
