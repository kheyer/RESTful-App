#!/usr/bin/env python3.7

# ======================
# Imports
# ======================
from flask import (Flask, render_template, request,
                   redirect, jsonify, url_for,
                   flash, make_response)
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker, scoped_session
from database_setup import *
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import os
import random
import string
import datetime
import json
import httplib2
import requests
from functools import wraps


# ======================
# App Name
# ======================
app = Flask(__name__)


# ======================
# Load Client Secrets
# ======================

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item-Catalog"

# ======================
# Database Connection
# ======================

engine = create_engine('sqlite:///item_database.db')
Base.metadata.bind = engine
session = scoped_session(sessionmaker(bind=engine))


@app.teardown_request
def remove_session(ex=None):
    session.remove()

# ======================
# Login protection
# ======================

# Login routing
def login_required(f):
    '''Checks if a user is logged in'''
    @wraps(f)
    def x(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return x


# Login page
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, input_id=CLIENT_ID)


# ======================
# Gconnect connect and disconnect
# ======================

# Oauth2 with gconnect to support login through google
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    # Store session data
    login_session['username'] = data.get('name', '')
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Check to see if user is already in the database
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """' " style = "width: 300px; height:
               300px;border-radius: 150px;-webkit-border-radius:
               150px;-moz-border-radius: 150px;"> '"""
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")

    return output


# Disconnect from google sign in
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']

        response = redirect(url_for('showCatalog'))
        flash("You are now logged out.")
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# ======================
# User data functions
# ======================

# Check database for user email
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Add new user to database
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Query user database by id
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one_or_none()
    return user


# ======================
# Main Page
# ======================

@app.route('/')
@app.route('/catalog/')
def showCatalog():
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('catalog.html', categories=categories)


# ======================
# Category Pages
# ======================

# Show specific category
@app.route('/catalog/<path:category_name>/')
@app.route('/catalog/<path:category_name>/items')
def showCategory(category_name):
    if category_name == 'items':
        return redirect(url_for('showAllItems'))

    categories = session.query(Category).order_by(asc(Category.name))

    # Redirect invalid URLs to main page
    try:
        category = session.query(Category).filter_by(name=category_name).one()
    except:
        return redirect(url_for('showCatalog'))

    items = session.query(
            Items).filter_by(category=category).order_by(asc(Items.name)).all()
    count = session.query(Items).filter_by(category=category).count()
    return render_template('categories.html',
                           category=category.name,
                           categories=categories,
                           items=items,
                           count=count)


# Add new category
@app.route('/catalog/addcategory', methods=['GET', 'POST'])
@login_required
def addCategory():
    if request.method == 'POST':
        # check to see if category exists
        if len(session.query(Category).filter_by(
                name=request.form['name']).all()) > 0:
            flash("Category '%s' already exists" % request.form['name'])
            return redirect(url_for('showCatalog'))

        else:
            newCategory = Category(name=request.form['name'],
                                   user_id=login_session['user_id'])
            session.add(newCategory)
            session.commit()
            flash('Category Added Successfully')
            return redirect(url_for('showCatalog'))
    else:
        return render_template('addcategory.html')


# Delete a category
@app.route('/catalog/<path:category_name>/delete', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_name):
    categoryToDelete = session.query(
                                Category).filter_by(name=category_name).one()
    # See if the logged in user is the owner of item
    creator = getUserInfo(categoryToDelete.user_id)
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot delete this Category. This Category belongs to %s"
              % creator.name)
        return redirect(url_for('showCatalog'))

    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        flash('Category %s Deleted! ' % categoryToDelete.name)
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deletecategory.html',
                               category=categoryToDelete)


# Edit a category
@app.route('/catalog/<path:category_name>/edit', methods=['GET', 'POST'])
@login_required
def editCategory(category_name):
    editedCategory = session.query(
                        Category).filter_by(name=category_name).one()
    old_name = editedCategory.name
    category = session.query(Category).filter_by(name=category_name).one()
    # See if the logged in user is the owner of item
    creator = getUserInfo(editedCategory.user_id)
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot edit this Category. This Category belongs to %s"
              % creator.name)
        return redirect(url_for('showCatalog'))

    if request.method == 'POST':
        if request.form['name']:
            if len(session.query(
                    Category).filter_by(name=request.form['name']).all()) > 0:
                flash('Category Name %s is Already Taken'
                      % request.form['name'])
                return redirect(url_for('showCatalog'))
            else:
                editedCategory.name = request.form['name']
        session.add(editedCategory)
        session.commit()
        flash('Category %s Edited to %s' % (old_name, editedCategory.name))
        return redirect(url_for('showCategory',
                                category_name=editedCategory.name))
    else:
        return render_template('editcategory.html',
                               category=category)


# ======================
# Item Pages
# ======================

# Display a Single Item
@app.route('/catalog/<path:category_name>/items/<path:item_name>/')
def showItem(category_name, item_name):
    item = session.query(Items).filter_by(name=item_name).one()
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('items.html',
                           item=item,
                           category=category_name,
                           categories=categories)


# Display all items in alphabetical order
@app.route('/catalog/items')
def showAllItems():
    items = session.query(Items).order_by(asc(Items.name)).all()
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('items_all.html',
                           items=items,
                           categories=categories)


# Add an item
@app.route('/catalog/add', methods=['GET', 'POST'])
@login_required
def addItem():
    categories = session.query(Category).all()
    if request.method == 'POST':
        newItem = Items(
            name=request.form['name'],
            description=request.form['description'],
            picture=request.form['picture'],
            category=session.query(
                    Category).filter_by(name=request.form['category']).one(),
            date=datetime.datetime.now(),
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('Item %s added to Category %s'
              % (newItem.name, newItem.category.name))
        return redirect(url_for('showCategory',
                                category_name=newItem.category.name))
    else:
        return render_template('additem.html',
                               categories=categories)


# Edit an item
@app.route('/catalog/<path:category_name>/items/<path:item_name>/edit',
           methods=['GET', 'POST'])
@login_required
def editItem(category_name, item_name):
    editedItem = session.query(Items).filter_by(name=item_name).one()
    categories = session.query(Category).all()
    # See if the logged in user is the owner of item
    creator = getUserInfo(editedItem.user_id)
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot edit this item. This item belongs to %s"
              % creator.name)
        return redirect(url_for('showCatalog'))
    if request.method == 'POST':
        # Not all forms are required - check to see what was updated
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['picture']:
            editedItem.picture = request.form['picture']
        if request.form['category']:
            category = session.query(
                    Category).filter_by(name=request.form['category']).one()
            editedItem.category = category
        time = datetime.datetime.now()
        editedItem.date = time
        session.add(editedItem)
        session.commit()
        flash('Item %s Successfully Edited' % editedItem.name)
        return redirect(url_for('showItem',
                                category_name=editedItem.category.name,
                                item_name=editedItem.name))
    else:
        return render_template('edititem.html',
                               item=editedItem,
                               categories=categories)


# Delete an item
@app.route('/catalog/<path:category_name>/items/<path:item_name>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteItem(category_name, item_name):
    itemToDelete = session.query(Items).filter_by(name=item_name).one()
    category = session.query(Category).filter_by(name=category_name).one()
    categories = session.query(Category).all()
    # See if the logged in user is the owner of item
    creator = getUserInfo(itemToDelete.user_id)
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot delete this item. This item belongs to %s"
              % creator.name)
        return redirect(url_for('showCatalog'))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Deleted item %s' % itemToDelete.name)
        return redirect(url_for('showCategory',
                                category_name=category.name))
    else:
        return render_template('deleteitem.html',
                               item=itemToDelete)


# ======================
# JSON Endpoints
# ======================

# All categories and items
@app.route('/catalog/JSON')
def allJSON():
    categories = [c.serialize for c in session.query(Category).all()]
    for i, c in enumerate(categories):
        it = session.query(Items).filter_by(category_id=c['id']).all()
        items = [i.serialize for i in it]

        if items:
            c['Items'] = items
    return jsonify(Category=categories)


# JSON for all categories
@app.route('/catalog/categories/JSON')
def categoriesJSON():
    categories = [c.serialize for c in session.query(Category).all()]
    return jsonify(categories=categories)


# JSON for all items within a category
@app.route('/catalog/<path:category_name>/items/JSON')
def categoryItemsJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = [i.serialize for i in session.query(
                                    Items).filter_by(category=category).all()]
    return jsonify(items=items)


# JSON for a single item
@app.route('/catalog/<path:category_name>/items/<path:item_name>/JSON')
def itemJSON(category_name, item_name):
    item = session.query(Items).filter_by(name=item_name).one()
    return jsonify(item=[item.serialize])

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
