from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import *
import datetime
import json

engine = create_engine('sqlite:///item_database.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Delete existing database contents for fresh start
session.query(Category).delete()
session.query(Items).delete()
session.query(User).delete()

file = open('data.json', 'r').read()
j = json.loads(file)

for new_user in j['Users']:
    New_User = User(name=new_user['name'],
                    email=new_user['email'],
                    picture=new_user['picture'])
    session.add(New_User)
    session.commit()

for cat in j['Categories']:
    New_Category = Category(name=cat['name'],
                            user_id=cat['user_id'])
    session.add(New_Category)
    session.commit()

for item in j['Items']:
    New_Item = Items(name=item['name'],
                     date=datetime.datetime.now(),
                     picture=item['picture'],
                     description=item['description'],
                     category_id=item['category_id'],
                     user_id=item['user_id'])
    session.add(New_Item)
    session.commit()

print("Database Population Complete")
