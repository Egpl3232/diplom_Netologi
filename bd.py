
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session
from config import db_url_object


metadata = MetaData()
base = declarative_base()
engine = create_engine(db_url_object)


class tablebot(base):
    __tablename__ = 'tablebot'
    user_id = sq.Column(sq.Integer, primary_key=True)
    searched_id = sq.Column(sq.Integer, primary_key=True)

def add_user(engine, user_id, searched_id):
    with Session(engine) as session:
        to_bd = tablebot(user_id=user_id, searched_id=searched_id)
        session.add(to_bd)
        session.commit()

def check_user(engine, user_id, searched_id):
    with Session(engine) as session:
        from_bd = session.query(tablebot).filter(
            tablebot.user_id == user_id,
            tablebot.searched_id == searched_id
        ).first()
        return True if from_bd else False


if __name__ == '__main__':
    base.metadata.create_all(engine)
