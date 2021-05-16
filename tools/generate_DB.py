import json
import logging
import queue
import threading

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from DB_Schema import Stop, Train, init_db
except:
    from tools.DB_Schema import Stop, Train, init_db

# config
THREAD_COUNT = 20
DB_URL = 'sqlite:///main1.db'
raw_data_file = 'raw_responses.json'
app_log_file = 'app.log'

# variables
trains_q = queue.Queue()
trains_schedule_q =queue.Queue()
complete_data = {  }

# lambdas
get_train_schedule = lambda train_no : requests.get(f'https://www.irctc.co.in/eticketing/protected/mapps1/trnscheduleenquiry/{train_no}', headers={'greq':'0'}).json()

# functions
def load_q(q, max_val, index, total_indices):
    cur_val = index
    if cur_val == 0:
        cur_val+=total_indices
    while cur_val < max_val:
        train_no = str(cur_val)
        train_no = '0'*(5-len(train_no)) + train_no
        q.put_nowait(train_no)
        print(f'\rloading data..  loaded: {q.qsize()}', end='           ')
        cur_val+=total_indices

def unload_q(unload_q, load_q):
    while unload_q.qsize():
        try:
            train_no = unload_q.get_nowait()
            print(f'\rfetching data.. remaining: {unload_q.qsize()}', end='                     ')
            train_data = get_train_schedule(train_no)
            complete_data[train_no] = train_data
            if 'errorMessage' in train_data:
                logging.info(f'{train_no} : {train_data["errorMessage"]}')
            else:
                load_q.put_nowait(train_data)
        except queue.Empty:
            return

def start(raw_response_file=None):
    logging.basicConfig(filename=app_log_file, filemode='w', format='%(asctime)s - %(threadName)s @ %(filename)s:%(lineno)d - %(message)s', level=logging.INFO)
    logging.info(f'start!')
    if raw_response_file:
        with open(raw_response_file) as file_cnx:
            complete_data = json.load(file_cnx)
        for train_no, train_data in complete_data.items():
            if 'errorMessage' in train_data:
                logging.info(f'{train_no} : {train_data["errorMessage"]}')
            else:
                trains_schedule_q.put_nowait(train_data)
        logging.info('data loaded from file!')
    else:
        threads_list = [ threading.Thread(target=load_q, args=(trains_q, 100000, i, THREAD_COUNT)) for i in range(THREAD_COUNT) ]
        for t_obj in threads_list:
            t_obj.start()
        for t_obj in threads_list:
            t_obj.join()
        logging.info('trains_list is prepared!')
        threads_list = [ threading.Thread(target=unload_q, args=(trains_q, trains_schedule_q)) for i in range(THREAD_COUNT) ]
        for t_obj in threads_list:
            t_obj.start()
        for t_obj in threads_list:
            t_obj.join()

    total_trains = trains_schedule_q.qsize()
    logging.info(f'trains_data is fetched! valid trains : {total_trains}')

    init_db(DB_URL)
    logging.info('DB initialised!')
    cur_session = sessionmaker(bind=create_engine(DB_URL))()
    while trains_schedule_q.qsize():
        try:
            cur_train_data = trains_schedule_q.get_nowait()
        except queue.Empty:
            break
        print(f'\rinserting to DB.. ( {total_trains-trains_schedule_q.qsize()}/{total_trains} )',end='            ')
        cur_session.add(
            Train(
                ID=cur_train_data['trainNumber'], 
                Name=cur_train_data['trainName'], 
                RunsOn= 1*(cur_train_data['trainRunsOnMon'] == 'Y') + 2*(cur_train_data['trainRunsOnTue'] == 'Y') + 4*(cur_train_data['trainRunsOnWed'] == 'Y') + 8*(cur_train_data['trainRunsOnTue'] == 'Y') + 16*(cur_train_data['trainRunsOnThu'] == 'Y') + 32*(cur_train_data['trainRunsOnFri'] == 'Y') + 64*(cur_train_data['trainRunsOnSat'] == 'Y') + 128*(cur_train_data['trainRunsOnSun'] == 'Y')
            )
        )
        if 'stationList' not in cur_train_data:
            logging.info(f'{cur_train_data["trainNumber"]} : No stations list')
            continue
        for stop_data in cur_train_data['stationList']:
            cur_session.add(
                Stop(
                    train_no = cur_train_data['trainNumber'],
                    route_no = stop_data['routeNumber'],
                    serial_no = stop_data['stnSerialNumber'],
                    station_code = stop_data['stationCode'],
                    station_name = stop_data['stationName'],	
                    distance = stop_data['distance'],
                    arr_day_cnt = int(stop_data['dayCount'])- (0 if '--' in (stop_data['departureTime'],stop_data['arrivalTime']) else (stop_data['departureTime']<stop_data['arrivalTime'])),
                    arr_time = stop_data['arrivalTime'] if stop_data['arrivalTime'] != '--' else None,
                    dept_day_cnt = stop_data['dayCount'],
                    dept_time = stop_data['departureTime'] if stop_data['departureTime'] != '--' else None,
                    halt_time =	stop_data['haltTime'] if stop_data['haltTime'] != '--' else None,
                )
            )
    cur_session.commit()
    cur_session.close()

    with open(raw_data_file, 'w') as file_cnx:
        json.dump(complete_data, file_cnx)
    logging.info(f'dumped to file: {raw_data_file}')
    print('\rall done!')
    logging.info(f'end!')
 
if __name__ == '__main__':
    start(r'resources\raw_responses.json')
