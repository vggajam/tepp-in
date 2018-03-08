
import datetime as dt
import logging
from flask import Flask, redirect, render_template, request, url_for
from db_tools import connect_to_aws,connect_local
from rendering_lib import *
from tepp import get_paths, seat_check
import json
# import threading
# from curr_avbl import curr_avbl
app = Flask(__name__)
# https://api.railwayapi.com/v2/check-seat/train/12001/source/BPL/dest/NDLS/date/16-07-2017/pref/CC/quota/GN/apikey/myapikey/
# db = connect_local()
db = connect_to_aws()

if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    app.debug = True
    app.run()
apikey = 'zhzygeldr2'
@app.route('/enquiry')
def enquiry():
    return render_template('enquiry.html')
# @app.route('/favicon.ico')
# def favicon():
#     return render_template('train.ico')

@app.route('/')
def index():
    return redirect(url_for('enquiry'))

@app.route('/service')
def service():
    return render_template('service.html')

# @app.route('/reg_submit',methods=['GET'])
# def get_curr_avbl():
#     src = str(request.args.get('src','')).split('-')[-1]
#     dst = str(request.args.get('dst','')).split('-')[-1]
#     date = str(request.args.get('jdate','')).split('-')
#     date = date[2]+'-'+date[1]+'-'+date[0]
#     clas = str(request.args.get('cls','')).split('-')[-1]
#     mobile = str(request.args.get('mobile',''))
#     print('coming')
#     mythread = threading.Thread(target=curr_avbl, args=(src,dst,date,clas,mobile))
#     mythread.start()
#     return 'temp'

@app.route('/seat_check',methods=['GET'])
def return_seat_avail():
    params = request.args
    sdt = (str(request.args['sdt']).split(' ')[0]).split('-')
    if sdt[2][0] == '0':
        sdt[2] = sdt[2][1]
    if sdt[1][0] == '0':
        sdt[1] = sdt[1][1]

    resp = dict()
    resp['rowid'] = str(params['rowid'])
    resp['key'] = str(params['key'])
    resp['seat']=str(seat_check(str(params['train_no']),str(params['src']),str(params['dst']),sdt[2]+'-'+sdt[1]+'-'+sdt[0],apikey,str(params['clas'])))
    # print(resp)
    return json.dumps(resp)
@app.route('/get_paths',methods=['GET'])
def get_paths_html():
    src = str(request.args.get('src','')).split('-')[-1]
    dst = str(request.args.get('dst','')).split('-')[-1]
    date = str(request.args.get('jdate','')).split('-')
    clas = str(request.args.get('cls','')).split('-')[-1]
    jdate=dt.datetime(int(date[0]),int(date[1]),int(date[2]))
    # print(src,dst,jdate)# pylint: disable=E1601
    
    trains_details = get_paths(src,dst,jdate, db)# pylint: disable=E1601
    responce_html =''
    if 'direct' in trains_details:
        results = render_direct_trains_row(trains_details['direct'])
        # print(results)# pylint: disable=E1601
        responce_html+= str(open('./templates/direct_train_table.html').read()).replace('{{tbody}}',results).replace('{{cls}}',clas)

    if 'one_stop' in trains_details:
        results = render_one_stop_row(trains_details['one_stop'])
        # print(results)# pylint: disable=E1601
        responce_html+=(str(open('./templates/one_stop_table.html').read()).replace('{{tbody}}',results).replace('{{cls}}',clas))
    print('resp',len(responce_html))
    return responce_html
@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500

