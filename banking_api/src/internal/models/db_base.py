from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


# Base database model
class Base(DeclarativeBase, MappedAsDataclass):
    pass
