# Item Catalog Project

This project runs a RESTful Flask application serving content stored in a SQL database. The app implements CRUD functionality protected by OAuth2, implemented for Google accounts. App content can also be accessed through a JSON endpoint.

## Contents

`app.py` runs the Flask application

`client_secrets.json` contains information for the OAuth2 token

`database_setup.py` sets up the SQL database

`database_populate.py` populates the database with some initial users, items and categories

`/templates` contains html files for the app

`/static` contains css files for the app

## Vagrant Setup

This app is designed to run on a Vagrant virtual machine. To set up the VM: 

1. Install [Vagrant](https://www.vagrantup.com/downloads.html)
2. Install [Virtual Box](https://www.virtualbox.org/)
3. Download the [Vagrant Configuration File](https://github.com/udacity/fullstack-nanodegree-vm/blob/master/vagrant/Vagrantfile)
4. In the terminal, run `vagrant up`
5. In the terminal, run `vagrant ssh`


## Running the Application
Once the VM is set up, run the following to start the app:

1. `python database_setup.py`
2. `python database_populate.py`
3. `python app.py`
4. Navigate to `http://localhost:5000/`
