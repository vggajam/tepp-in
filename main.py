import flask
import DBRC
import datetime
from SQL_queries import *

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
DBRC.db.init_app(app)

MAX_EACH_TYPE_LIMIT = 100
MAX_RESULTS = 100

str_time_delta = lambda time_delta: (str(time_delta).replace(':', ' hrs ', 1)[:-3]+' mins').replace('00 mins', '')

@app.route("/")
def homepage():
    return flask.redirect(flask.url_for('search'))

@app.route("/enquiry", methods=['GET','POST'])
def search():
    fromStn = ''
    toStn = ''
    startDate = datetime.datetime.now().isoformat()[:10]
    stations = None
    search_results = None
    with DBRC.db.engine.connect() as db_cnx:
        stations = db_cnx.execute(SQL_STATIONS_LIST).all()
        if flask.request.method == 'POST':
            fromStn = flask.request.form.get('fromStn')
            toStn = flask.request.form.get('toStn')
            startDate = datetime.date.fromisoformat(flask.request.form.get('startDate'))
            weekday = startDate.weekday()
            search_results = []
            for cur_db_row in db_cnx.execute(SQL_DIRECT_TRAINS, {'fromStn':fromStn[:fromStn.index(' - ')], 'toStn':toStn[:toStn.index(' - ')], 'weekday':weekday}):
                cur_row = { 'type' : 1 }
                for idx in range(len(cur_db_row)):
                    cur_row[list(cur_db_row.keys())[idx]] = cur_db_row[idx]
                cur_row['src_date'] = startDate.strftime('%d %b (%a)')
                cur_row['dest_date'] = (startDate+datetime.timedelta(days=cur_db_row['dest_day_cnt']-cur_db_row['src_day_cnt'])).strftime('%d %b (%a)')
                cur_row['total_time'] = ( datetime.datetime.strptime(f"{cur_db_row['dest_day_cnt']} {cur_db_row['dest_arr_time']}", "%d %H:%M") - datetime.datetime.strptime(f"{cur_db_row['src_day_cnt']} {cur_db_row['src_dept_time']}", "%d %H:%M") )
                cur_row['total_time_str'] = str_time_delta(cur_row['total_time'])
                cur_row['total_time_in_seconds'] = cur_row['total_time'].total_seconds()
                search_results.append(cur_row)
            cnt = 0
            for cur_db_row in db_cnx.execute(SQL_TWO_CONNECTING_TRAINS, {'fromStn':fromStn[:fromStn.index(' - ')], 'toStn':toStn[:toStn.index(' - ')], 'weekday':weekday}):
                if cnt >= MAX_EACH_TYPE_LIMIT or len(search_results) > MAX_RESULTS: 
                    break
                days_delta = cur_db_row['train1_dest_day_cnt'] - cur_db_row['train1_src_day_cnt'] + (cur_db_row['train1_dest_arr_time']>cur_db_row['train2_src_dept_time'])
                train2_src_date = startDate+datetime.timedelta(days=days_delta)
                if not (cur_db_row['train2_runson'] & (1<<train2_src_date.weekday())):
                    continue
                cur_row = { 'type' : 2 }
                for idx in range(len(cur_db_row)):
                    cur_row[list(cur_db_row.keys())[idx]] = cur_db_row[idx]
                cur_row['train1_src_date'] = startDate.strftime('%d %b (%a)')
                cur_row['train1_dest_date'] = (startDate+datetime.timedelta(days=cur_db_row['train1_dest_day_cnt']-cur_db_row['train1_src_day_cnt'])).strftime('%d %b (%a)')
                cur_row['train1_time'] = ( datetime.datetime.strptime(f"{cur_db_row['train1_dest_day_cnt']} {cur_db_row['train1_dest_arr_time']}", "%d %H:%M") - datetime.datetime.strptime(f"{cur_db_row['train1_src_day_cnt']} {cur_db_row['train1_src_dept_time']}", "%d %H:%M") )
                cur_row['train1_time_str'] = str_time_delta(cur_row['train1_time'])
                cur_row['train2_src_date'] = train2_src_date.strftime('%d %b (%a)')
                cur_row['train2_dest_date'] = (train2_src_date+datetime.timedelta(days=cur_db_row['train2_dest_day_cnt']-cur_db_row['train2_src_day_cnt'])).strftime('%d %b (%a)')
                cur_row['train2_time'] = ( datetime.datetime.strptime(f"{cur_db_row['train2_dest_day_cnt']} {cur_db_row['train2_dest_arr_time']}", "%d %H:%M") - datetime.datetime.strptime(f"{cur_db_row['train2_src_day_cnt']} {cur_db_row['train2_src_dept_time']}", "%d %H:%M") ) 
                cur_row['train2_time_str'] = str_time_delta(cur_row['train2_time'])
                cur_row['wait_time'] = ( datetime.datetime.strptime(f"{1+int(cur_db_row['train2_src_dept_time'] < cur_db_row['train1_dest_arr_time'])} {cur_db_row['train2_src_dept_time']}", "%d %H:%M") - datetime.datetime.strptime(f"1 {cur_db_row['train1_dest_arr_time']}", "%d %H:%M") )
                cur_row['total_time'] = cur_row['train1_time'] + cur_row['train2_time'] + cur_row['wait_time']
                cur_row['total_time_str'] = str_time_delta(cur_row['total_time'])
                cur_row['total_time_in_seconds'] = cur_row['total_time'].total_seconds()
                search_results.append(cur_row)
                cnt+=1
            search_results = sorted(search_results, key= lambda pkt: pkt['total_time_in_seconds'])
    return flask.render_template(
        'search.html', 
        fromStn = fromStn,
        toStn = toStn,
        startDate = startDate,
        stations= stations,
        search_results= search_results
    )

@app.route("/facts", methods=['GET'])
def facts():
    FACTS_MAP = {
        '5': {
            'QUEST' : 'Top 10 stations with most trains stop by',
            'SQL_QRY':SQL_STATION_WITH_MOST_TRAINS
        },
        '1': {
            'QUEST': 'Top 10 trains with most stops',
            'SQL_QRY': SQL_TRAIN_WITH_MOST_STOPS
        },
        '4': {
            'QUEST' : 'Top 10 trains that travel most distance in its trip',
            'SQL_QRY':SQL_TRAIN_WITH_MAX_DISTANCE
        },
        '2': {
            'QUEST': 'Top 10 trains with least stops',
            'SQL_QRY': SQL_TRAIN_WITH_LEAST_STOPS
        },
        '3': {
            'QUEST' : 'Top 10 trains that travel least in its trip',
            'SQL_QRY': SQL_TRAIN_WITH_LEAST_DISTANCE
        },
    }
    with DBRC.db.engine.connect() as db_cnx:
        for qid, pkt in FACTS_MAP.items():
            FACTS_MAP[qid]['ANS'] = [ cur_db_row['statement'] for cur_db_row in db_cnx.execute(pkt['SQL_QRY'], {'limit':10}) ]
    return flask.render_template('facts.html', goback=1,facts=FACTS_MAP)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=1)