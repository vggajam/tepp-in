import json
import logging
import queue
import threading
import bs4
import requests
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# config
THREAD_COUNT = 20
SCHEDULE_API = 'mntes' # 'irctc' or 'mntes'

# schema
Base = declarative_base()

class Train(Base):
    __tablename__ = 'trains'

    ID = Column(String, primary_key=1)
    Name = Column(String)
    RunsOn = Column(Integer, nullable=0)

    def __repr__(self):
        run_days = []
        weekdays = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
        for idx in range(len(weekdays)):
            if self.RunsOn & (1 <<idx):
                run_days.append(weekdays[idx])
        run_days_str = ', '.join(run_days)
        return f'<Train (ID="{self.ID}", Name="{self.Name}", RunsOn="{run_days_str}")>'

class Stop(Base):
    __tablename__ = 'stops'

    train_no = Column(String, ForeignKey('trains.ID'), primary_key=1)
    route_no = Column(Integer, primary_key=1)
    serial_no = Column(Integer, primary_key=1)
    station_code = Column(String)
    station_name = Column(String)
    distance = Column(Integer)
    arr_day_cnt = Column(Integer)	
    arr_time = Column(String)
    dept_day_cnt = Column(Integer)
    dept_time = Column(String)
    halt_time =	Column(String)

    def __repr__(self):
        return f'<Stop (train_no="{self.train_no}, route_no="{self.route_no}", serial_no="{self.serial_no}", station_code="{self.station_code}") >'

# lambdas
get_train_schedule_from_irctc = lambda train_no : requests.get(f'https://www.irctc.co.in/eticketing/protected/mapps1/trnscheduleenquiry/{train_no}', headers={'greq':'0'}).json()

# functions
def get_train_schedule_from_mntes(train_no):
    for day_idx in range(14):
        try:
            resp = requests.post(f"https://enquiry.indianrail.gov.in/mntes/q?opt=TrainServiceSchedule&subOpt=show&trainNo={train_no}", data={"trainNo":f"{train_no}-", "trainStartDate": f"0{1+day_idx}-Jun-2030"})
            soup = bs4.BeautifulSoup(resp.text,'html.parser')
            train_tbody, schedule_tbody = soup.find_all('tbody')
            ret_val = {}
            for td in train_tbody.find_all('td'):
                td_text = td.text.strip() 
                if td_text.startswith('Days of Run:'):
                    ret_val['trainRunsOn'] = td_text.replace('Days of Run:','').strip()
                    logging.info(ret_val['trainRunsOn'])
                elif td_text.startswith('Type:'):
                    ret_val['trainType'] = td_text.replace('Type:','').strip()
                elif td_text.startswith(train_no):
                    ret_val['trainNumber'] = train_no
                    ret_val['trainName'] = td_text.replace(train_no,'').strip()
            trs = schedule_tbody.find_all('tr')
            dict_keys = [td.text.strip() for td in trs[0].find_all('td') ]
            ret_val['stops'] = []
            for row in trs[1:]:
                tds = row.find_all('td')
                ret_val['stops'].append({ dict_keys[idx]: tds[idx].text.strip() for idx in range(len(tds)) })
            return ret_val
        except:
            #logging.warning('error!', exc_info=1)
            pass
    return { 'errorMessage':'Unknown error!'}

def fetch_and_load_train_schedule_q(train_list_q, train_schedule_list_q):

    while train_list_q.qsize():
        try:
            train_no = train_list_q.get_nowait()
        except queue.Empty:
            logging.info('train_list_q is empty!')
            break
        logging.debug(f'fetching train schedule: {train_no}')
        print(f'\rfetching train schedule: {train_no} , qsize: {train_list_q.qsize()} ', end='')
        if SCHEDULE_API == 'irctc':
            train_schedule = get_train_schedule_from_irctc(train_no)
            if 'errorMessage' in train_schedule:
                logging.info(f'{train_no} : {train_schedule["errorMessage"]}')
            else:
                train_schedule_list_q.put_nowait(train_schedule)
        elif SCHEDULE_API == 'mntes':
            train_schedule = get_train_schedule_from_mntes(train_no)
            if 'errorMessage' in train_schedule:
                logging.info(f'{train_no} : {train_schedule["errorMessage"]}')
            else:
                train_schedule_list_q.put_nowait(train_schedule)
        else:
            logging.error(f'Unknown SCHEDULE_API : {SCHEDULE_API}')
            return -1

def generate_db(db_file):
    
    train_list_q = queue.SimpleQueue()
    for i in range(1,100000):
        train_no = str(i)
        train_no_str = '0'*(5-len(train_no)) + train_no
        train_list_q.put_nowait(train_no_str)
    logging.info(f'train_list_q is prepared. qsize: {train_list_q.qsize()}')

    train_schedule_list_q = queue.SimpleQueue()
    fetching_threads = [ threading.Thread(target=fetch_and_load_train_schedule_q, args=(train_list_q, train_schedule_list_q)) for i in range(THREAD_COUNT) ]
    [ cur_thread.start() for cur_thread in fetching_threads ]
    [ cur_thread.join() for cur_thread in fetching_threads ]
    logging.info(f'train_schedule_list_q is prepared. qsize: {train_schedule_list_q.qsize()}')
    
    DB_URL = f'sqlite:///{db_file}'
    db_engine = create_engine(DB_URL)
    Base.metadata.create_all(db_engine)
    logging.info('db initialised!')

    cur_db_session = sessionmaker(bind=db_engine)()
    try:
        while train_schedule_list_q.qsize():
            try:
                cur_train_schedule = train_schedule_list_q.get_nowait()
            except queue.Empty:
                logging.info('train_schedule_list_q is empty!')
                break
            print(f'\rUpdating DB. remaining queue size: {train_schedule_list_q.qsize()}',end='')
            if SCHEDULE_API == 'irctc':
                cur_db_session.add(
                    Train(
                        ID=cur_train_schedule['trainNumber'], 
                        Name=cur_train_schedule['trainName'], 
                        RunsOn= 1*(cur_train_schedule['trainRunsOnMon'] == 'Y') + 2*(cur_train_schedule['trainRunsOnTue'] == 'Y') + 4*(cur_train_schedule['trainRunsOnWed'] == 'Y') + 8*(cur_train_schedule['trainRunsOnTue'] == 'Y') + 16*(cur_train_schedule['trainRunsOnThu'] == 'Y') + 32*(cur_train_schedule['trainRunsOnFri'] == 'Y') + 64*(cur_train_schedule['trainRunsOnSat'] == 'Y') + 128*(cur_train_schedule['trainRunsOnSun'] == 'Y')
                    )
                )
                if 'stationList' not in cur_train_schedule:
                    logging.info(f'{cur_train_schedule["trainNumber"]} : No stations list')
                    continue
                for stop_data in cur_train_schedule['stationList']:
                    cur_db_session.add(
                        Stop(
                            train_no = cur_train_schedule['trainNumber'],
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
            elif SCHEDULE_API == 'mntes':
                if cur_train_schedule['trainRunsOn'] == 'Daily':
                    run_days = 127
                else:
                    trainRunsOn = cur_train_schedule['trainRunsOn'].lower()
                    run_days = 1*('mon' in trainRunsOn) + 2*('tue' in trainRunsOn) + 4*('wed' in trainRunsOn) + 8*('thu' in trainRunsOn) + 16*('fri' in trainRunsOn) + 32*('sat' in trainRunsOn) + 64*('sun' in trainRunsOn)
                cur_db_session.add(
                    Train(
                        ID = cur_train_schedule['trainNumber'],
                        Name = cur_train_schedule['trainName'],
                        RunsOn = run_days
                    )
                )
                if not cur_train_schedule.get('stops'):
                    logging.info(f'{cur_train_schedule["trainNumber"]} : No stations list')
                    continue
                for cur_stop in cur_train_schedule['stops']:
                    cur_db_session.add(
                        Stop(
                            train_no = cur_train_schedule['trainNumber'],
                            route_no = 1,
                            serial_no = cur_stop['Sr.'],
                            station_code = cur_stop['Code'],
                            station_name = cur_stop['Station'],	
                            distance = cur_stop['Dist.'],
                            arr_day_cnt = int(cur_stop['Day'])- (0 if '' in  (cur_stop['Dep.'],cur_stop['Arr.']) else (cur_stop['Dep.']<cur_stop['Arr.'])),
                            arr_time = cur_stop['Arr.'] if cur_stop['Arr.'] else None,
                            dept_day_cnt = cur_stop['Day'],
                            dept_time = cur_stop['Dep.'] if cur_stop['Dep.'] else None,
                            halt_time =	None,
                        )
                    )
                pass
            else:
                logging.error(f'Unknown SCHEDULE_API : {SCHEDULE_API}')
                return -1
        print('done!')
    finally:
        cur_db_session.close()

if __name__ == '__main__':
    logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(threadName)s @ %(filename)s:%(lineno)d - %(message)s', level=logging.INFO)
    logging.info(f'start!')
    generate_db('main1.db')
    # start(r'resources\raw_responses.json')
