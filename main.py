
import datetime as dt
import logging
import os
import json

import MySQLdb
from flask import Flask, redirect, render_template, request, url_for

from rendering_lib import *
from tepp import get_paths

# These environment variables are configured in app.yaml.
CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
CLOUDSQL_USER = os.environ.get('CLOUDSQL_USER')
CLOUDSQL_PASSWORD = os.environ.get('CLOUDSQL_PASSWORD')
CLOUDSQL_DB = os.environ.get('CLOUDSQL_DB')
def connect_to_cloudsql():
    # When deployed to App Engine, the `SERVER_SOFTWARE` environment variable
    # will be set to 'Google App Engine/version'.
    if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
        # Connect using the unix socket located at
        # /cloudsql/cloudsql-connection-name.
        cloudsql_unix_socket = os.path.join('/cloudsql', CLOUDSQL_CONNECTION_NAME)

        db = MySQLdb.connect(unix_socket=cloudsql_unix_socket, user=CLOUDSQL_USER, passwd=CLOUDSQL_PASSWORD, db=CLOUDSQL_DB)

    # If the unix socket is unavailable, then try to connect using TCP. This
    # will work if you're running a local MySQL server or using the Cloud SQL
    # proxy, for example:
    #
    #   $ cloud_sql_proxy -instances=your-connection-name=tcp:3306
    #
    else:
        db = MySQLdb.connect(host='127.0.0.1', user=CLOUDSQL_USER, passwd=CLOUDSQL_PASSWORD,db=CLOUDSQL_DB)

    return db

def connect_local():
    db_details = json.load(open('./mysql_details.json'))
    return MySQLdb.connect(host=db_details['host'],user = db_details['user'], port=db_details['port'],passwd=db_details['passwd'],db=db_details['db'])

app = Flask(__name__)

@app.route('/enquiry.html')
def enquiry():
    return render_template('enquiry.html')
@app.route('/favicon.ico')
def favicon():
    return render_template('train.ico')

@app.route('/')
def index():
    return redirect(url_for('enquiry'))

@app.route('/service.html')
def service():
    return render_template('service.html')

@app.route('/get_paths.html',methods=['GET'])
def get_paths_html():
    src = str(request.args.get('src','')).split('-')[-1]
    dst = str(request.args.get('dst','')).split('-')[-1]
    date = str(request.args.get('jdate','')).split('-')
    jdate=dt.datetime(int(date[0]),int(date[1]),int(date[2]))
    # print(src,dst,jdate)# pylint: disable=E1601
    db = connect_to_cloudsql()
    # db = connect_local()
    trains_details = get_paths(src,dst,jdate, db)# pylint: disable=E1601
    responce_html =''
    if 'direct' in trains_details:
        results = render_direct_trains_row(trains_details['direct'],src,dst,jdate)
        # print(results)# pylint: disable=E1601
        responce_html+= str(open('./templates/direct_train_table.html').read()).replace('{{tbody}}',results)

    if 'one_stop' in trains_details:
        results = render_one_stop_row(trains_details['one_stop'],src, dst, jdate)
        # print(results)# pylint: disable=E1601
        responce_html+=str(open('./templates/one_stop_table.html').read()).replace('{{tbody}}',results)
    return responce_html
@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500

# [END form]

# @app.route('/station_list.js',methods=['GET'])
# app.get('/station_list.js', function(req, res) {
# 	res.render('station_list.js');
# });
# [START submitted]
# @app.route('/submitted', methods=['POST'])
# def submitted_form():
#     name = request.form['name']
#     email = request.form['email']
#     site = request.form['site_url']
#     comments = request.form['comments']

#     # [END submitted]
#     # [START render_template]
#     return render_template(
#         'submitted_form.html',
#         name=name,
#         email=email,
#         site=site,
#         comments=comments)
#     # [END render_template]


# [END app]
