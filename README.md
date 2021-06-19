# Train Enquiry Web App for Indian Railways

Currently hosted in gcloud at https://tepp-in.el.r.appspot.com

## Features :
- Shows the direct trains and **connecting trains** from Source to Destination for a given date at https://tepp-in.el.r.appspot.com/enquiry
- Shows some interesting facts of indian railways at https://tepp-in.el.r.appspot.com/facts

## Frameworks and tools used:
- [Flask](https://flask.palletsprojects.com/)
- [SQLite](https://www.sqlite.org/)
- [Flask-sqlalchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [requests](https://docs.python-requests.org/)
- [Material Design Lite](https://getmdl.io/)

## How it works :
- Train schedule for all trains is scrapped from irctc/mntes website and stored in sqlite database.  check out ```DB_tools.py``` for the same.
- Web app queries the database and shows the results. checkout ```main.py``` for the same
