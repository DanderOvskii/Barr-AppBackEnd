from sqlmodel import Session, select
from models import Items


def get_items(session: Session):
    return session.exec(select(Items)).all()

