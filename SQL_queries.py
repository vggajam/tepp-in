SQL_STATIONS_LIST = """
select distinct stops.station_code||' - '|| stops.station_name
from stops;
"""
SQL_DIRECT_TRAINS = """
select train.ID as train_no,
train.Name as train_name,
src.route_no as route_no,
src.serial_no as src_serial_no,
src.station_code as src_station_code,
src.station_name as src_station_name,
src.distance as src_distance,
src.dept_day_cnt as src_day_cnt,
src.dept_time as src_dept_time,
dest.serial_no as dest_serial_no,
dest.station_code as dest_station_code,
dest.station_name as dest_station_name,
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


# facts
SQL_TRAIN_WITH_MOST_STOPS = """
SELECT trains.Name||' - '||stops.train_no||' ('||(count(DISTINCT stops.station_code))||' stops)' as statement,
trains.Name,
stops.train_no,
count(DISTINCT stops.station_code) as station_cnt,
max(stops.distance) as max_distance
from stops
JOIN trains
on stops.train_no = trains.ID
group by trains.ID
order by station_cnt desc, max_distance desc
limit :limit;
"""
SQL_TRAIN_WITH_LEAST_STOPS = """
SELECT trains.Name||' - '||stops.train_no||' ('||(count(DISTINCT stops.station_code))||' stops, '||(max(stops.distance))||' kms)' as statement,
trains.Name as train_name,
stops.train_no as train_no,
count(DISTINCT stops.station_code) as station_cnt,
max(stops.distance) as max_distance
from stops
JOIN trains
on stops.train_no = trains.ID
group by trains.ID
order by station_cnt asc, max_distance asc
limit :limit;
"""
SQL_TRAIN_WITH_LEAST_DISTANCE = """
SELECT trains.Name||' - '||trains.ID||' ('||max(stops.distance)||' kms) ' as statement,
trains.Name as train_name,
stops.train_no as train_no,
count(DISTINCT stops.station_code) as station_cnt,
max(stops.distance) as max_distance
from stops
JOIN trains
on stops.train_no = trains.ID
group by trains.ID
order by max_distance , station_cnt
limit :limit;
"""
SQL_TRAIN_WITH_MAX_DISTANCE = """
SELECT trains.Name||' - '||trains.ID||' ('||max(stops.distance)||' kms) ' as statement,
trains.Name as train_name,
stops.train_no as train_no,
count(DISTINCT stops.station_code) as station_cnt,
max(stops.distance) as max_distance,
max(stops.arr_day_cnt) as max_days
from stops
JOIN trains
on stops.train_no = trains.ID
group by trains.ID
order by max_distance desc, max_days desc, station_cnt desc
limit :limit;
"""
SQL_STATION_WITH_MOST_TRAINS = """
SELECT stops.station_code||' - '||stops.station_name||' ('||count(distinct stops.train_no)||' trains)' as statement,
stops.station_code,
stops.station_name,
count(distinct stops.train_no) as trains_cnt
from stops
group by stops.station_code
order by trains_cnt desc
limit :limit;
"""