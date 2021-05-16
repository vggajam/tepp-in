
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
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
 
def init_db(URL='sqlite:///main.db'):
    from sqlalchemy import create_engine
    Base.metadata.create_all(create_engine(URL))
