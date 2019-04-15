#!/usr/bin/env python3.7
# Database setup script
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    """Creates user information table"""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    """Creates category information table"""
    __tablename__ = "category"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""

        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id
        }


class Items(Base):
    """Creates item information table"""
    __tablename__ = "item"

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(String(500))
    picture = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category,
                            backref=backref('item', cascade='all,delete'))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'picture': self.picture,
            'category_id': self.category_id
        }


engine = create_engine('sqlite:///item_database.db')
Base.metadata.create_all(engine)
