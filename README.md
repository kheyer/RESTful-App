# RESTful Web Application

This project runs a RESTful Flask application serving content stored in a SQL database. The app implements CRUD functionality protected by OAuth2, implemented for Google accounts. App content can also be accessed through a JSON endpoint.

## Contents

`app.py` runs the Flask application

`client_secrets_fake.json` example of an OAuth2 token used for authentication. A real token must be generated to run the application with full login support

`database_setup.py` sets up the SQL database

`database_populate.py` populates the database with some initial users, items and categories

`/templates` contains html files for the app

`/static` contains css files for the app

# Setup

## OAuth2 Through Google Sign-In

To implement OAuth2 sign-in through google, you need a proper Client ID from [Google](https://console.developers.google.com/apis/credentials). A real auth token is not provided in the repository. Once an authentication token is acquired, it should be configured to work with port 5000.

   * Add `http://localhost:5000` to `Authorized JavaScript origins`
   * Add `http://localhost:5000/gconnect` to `Authorized redirect URIs`
   * Add `http://localhost:5000/login` to `Authorized redirect URIs`
   
The configured token should be downloaded as a json file and placed in the `app.py` directory

## Database Setup

Run the following to create the sqlite database and populate it with some initial items:
   * `python database_setup.py`
   * `python database_populate.py`

## Running the Application

Once the database setup is complete, start the app by doing the following:

   * `python app.py`
   * Navigate to `http://localhost:5000/` in a browser
