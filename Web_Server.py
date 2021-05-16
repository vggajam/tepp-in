import flask
import DBRC
import datetime

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
DBRC.db.init_app(app)

ROWS_LIMIT = 100

# SQL Queries
SQL_STATIONS_LIST = """
select distinct stops.station_code, stops.station_name
from stops;
"""
SQL_DIRECT_TRAINS = """
select train.ID as train_no,
train.Name as train_name,
src.route_no as route_no,
src.serial_no as src_serial_no,
src.station_code as src_station_code,
src.distance as src_distance,
src.dept_day_cnt as src_day_cnt,
src.dept_time as src_dept_time,
dest.serial_no as dest_serial_no,
dest.station_code as dest_station_code,
dest.distance as dest_distance,
dest.arr_day_cnt as dest_day_cnt,
dest.arr_time as dest_arr_time,
dest.distance - src.distance as travel_distance
from stops as src 
JOIN stops as dest 
on src.train_no = dest.train_no
and src.route_no = dest.route_no
and src.serial_no < dest.serial_no
JOIN trains as train
on src.train_no = train.ID
WHERE src.station_code = :fromStn
and dest.station_code = :toStn
and train.RunsOn & (1 << ((21+:weekday-(src.dept_day_cnt-1))%7))  > 0;
"""

SQL_TWO_CONNECTING_TRAINS = """
select train1.ID as train1_no,
train1.Name as train1_name,
train1.RunsOn as train1_runson,
train1_src.station_code as train1_src_code,
train1_src.station_name as train1_src_name,
train1_src.dept_day_cnt as train1_src_day_cnt,
train1_src.distance as train1_src_distance,
train1_src.dept_time as train1_src_dept_time,
train1_dest.station_code as train1_dest_code,
train1_dest.station_name as train1_dest_name,
train1_dest.arr_day_cnt as train1_dest_day_cnt,
train1_dest.distance as train1_dest_distance,
train1_dest.arr_time as train1_dest_arr_time,
train2.ID as train2_no,
train2.Name as train2_name,
train2.RunsOn as train2_runson,
train2_src.station_code as train2_src_code,
train2_src.station_name as train2_src_name,
train2_src.dept_day_cnt as train2_src_day_cnt,
train2_src.distance as train2_src_distance,
train2_src.dept_time as train2_src_dept_time,
train2_dest.station_code as train2_dest_code,
train2_dest.station_name as train2_dest_name,
train2_dest.arr_day_cnt as train2_dest_day_cnt,
train2_dest.distance as train2_dest_distance,
train2_dest.arr_time as train2_dest_arr_time,
(train2_dest.distance - train2_src.distance + train1_dest.distance - train1_src.distance) as travel_distance
from stops as train1_src
JOIN stops as train1_dest
on train1_src.train_no = train1_dest.train_no
and train1_src.route_no = train1_dest.route_no
and train1_src.serial_no < train1_dest.serial_no
JOIN trains as train1
on train1_src.train_no = train1.ID
JOIN stops as train2_src
on train1_dest.station_code = train2_src.station_code
JOIN stops as train2_dest
on train2_src.train_no = train2_dest.train_no
and train2_src.route_no = train2_dest.route_no
and train2_src.serial_no < train2_dest.serial_no
JOIN trains as train2
on train2_src.train_no = train2.ID
WHERE train1.ID != train2.ID
and train1_src.station_code = :fromStn
and train2_dest.station_code = :toStn
and train1.RunsOn & (1 << ((21+:weekday -(train1_src.dept_day_cnt-1))%7))  > 0
order by travel_distance
;"""

@app.route("/")
def homepage():
    return flask.redirect(flask.url_for('search'))

@app.route("/search", methods=['GET','POST'])
def search():
    stations = None
    search_results = None
    with DBRC.db.engine.connect() as db_cnx:
        stations = db_cnx.execute(SQL_STATIONS_LIST).all()
        if flask.request.method == 'POST':
            fromStn = flask.request.form.get('fromStn')
            toStn = flask.request.form.get('toStn')
            start_date = datetime.date.fromisoformat(flask.request.form.get('startDate'))
            weekday = start_date.weekday()
            search_results = []
            for cur_db_row in db_cnx.execute(SQL_DIRECT_TRAINS, {'fromStn':fromStn, 'toStn':toStn, 'weekday':weekday}):
                cur_row = { 'type' : 1 }
                for idx in range(len(cur_db_row)):
                    cur_row[list(cur_db_row.keys())[idx]] = cur_db_row[idx]
                cur_row['src_date'] = start_date.strftime('%d %b (%a)')
                cur_row['dest_date'] = (start_date+datetime.timedelta(days=cur_db_row['dest_day_cnt']-cur_db_row['src_day_cnt'])).strftime('%d %b (%a)')
                search_results.append(cur_row)
            cnt = 0
            for cur_db_row in db_cnx.execute(SQL_TWO_CONNECTING_TRAINS, {'fromStn':fromStn, 'toStn':toStn, 'weekday':weekday}):
                if cnt >= ROWS_LIMIT:
                    break
                days_delta = cur_db_row['train1_dest_day_cnt'] - cur_db_row['train1_src_day_cnt'] + (cur_db_row['train1_dest_arr_time']>cur_db_row['train2_src_dept_time'])
                train2_src_date = start_date+datetime.timedelta(days=days_delta)
                if cur_db_row['train2_runson'] & (1<<train2_src_date.weekday()):
                    continue
                cur_row = { 'type' : 2 }
                for idx in range(len(cur_db_row)):
                    cur_row[list(cur_db_row.keys())[idx]] = cur_db_row[idx]
                cur_row['train1_src_date'] = start_date.strftime('%d %b (%a)')
                cur_row['train1_dest_date'] = (start_date+datetime.timedelta(days=cur_db_row['train1_dest_day_cnt']-cur_db_row['train1_src_day_cnt'])).strftime('%d %b (%a)')
                cur_row['train2_src_date'] = train2_src_date.strftime('%d %b (%a)')
                cur_row['train2_dest_date'] = (train2_src_date+datetime.timedelta(days=cur_db_row['train2_dest_day_cnt']-cur_db_row['train2_src_day_cnt'])).strftime('%d %b (%a)')
                search_results.append(cur_row)
                cnt+=1
    return flask.render_template(
        'search.html', 
        stations= stations,
        search_results= search_results
    )

@app.route("/funfacts", methods=['GET'])
def funfacts():
    for x in DBRC.Train.query.all():
        print(x)
    return ''

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=1)