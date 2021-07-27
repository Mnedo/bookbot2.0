import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()

__factory = None


def global_init():
    global __factory

    if __factory:
        return

    conn_str = 'postgresql://ftdnlgfgkosezq:7a0009560ec3deac4c1b553cd1f7c5a381e786a4c5f1c5ca69c03b5c18e48003@ec2-52-19-170-215.eu-west-1.compute.amazonaws.com:5432/deeltkp3h0un4n'

    print(f"Подключение к базе данных по адресу {conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()
