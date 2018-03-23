"""
    mysql tools
"""
import os
import json

import MySQLdb
def connect_to(creds_file):
    db_creds = json.load(open(creds_file))
    return MySQLdb.connect(host=db_creds['host'], user=db_creds['user'], port= db_creds['port'], passwd=db_creds['passwd'],db=db_creds['db'])

weekdays = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
def week_day_code( weekday):
    if type(weekday) is type(0):
        if weekday<7 and weekday >=0 :
            weekday = weekdays[weekday]
        else:
            print('invalid weekday') # pylint: disable=E1601
            return None,None
    elif type(weekday) == type('MON'):
        if weekday not in weekdays:
            print('invalid weekday!') # pylint: disable=E1601
            return None,None
    return weekday,weekdays.index(weekday)

inter_stns_query = """ select stations.stn_code, stations.trains_cnt from hops inner join stations on hops.stn_code = stations.stn_code where train_no = %s and hop_index > 0+%s and hop_index < 0+%s and stations.trains_cnt>39"""
def inter_stns(src, dst, weekday, db):
    weekday,_ = week_day_code(weekday)
    if weekday is None:
        return None, None
    trains = trains_btw_with_times(src, dst, weekday, db)
    if trains is None:
        print('No trains btw',src,dst)# pylint: disable=E1601
        return None,None
    stns_list = dict()
    ptr = db.cursor()
    for tpl in trains:
        ptr.execute(inter_stns_query,(tpl[0],tpl[1],tpl[2]))
        for row in ptr:
            stns_list[row[0]]=int(row[1])
    stns_list_sorted = sorted(list(stns_list.items()), key = lambda x: x[1], reverse=True)
    return stns_list_sorted,trains

trains_btw_with_times_qry = "select trains.train_no,src.hop_index,dst.hop_index, src.arr_time, src.dept_time, dst.arr_time, dst.dept_time, src.day, dst.day from (hops as src inner join hops as dst on src.train_no = dst.train_no inner join trains on src.train_no = trains.train_no) where src.hop_index < dst.hop_index and src.stn_code = %s and dst.stn_code = %s and trains.%w = 1 and src.day = %s"
def trains_btw_with_times(src, dst, weekday, db):
    weekday,week_day_no = week_day_code(weekday)
    if weekday is None:
        return None, None
    ptr = db.cursor()
    result = list()
    for i in range(5):
        qry = trains_btw_with_times_qry.replace('%w',weekdays[(week_day_no-i+7)%7])
        ptr.execute(qry,(src,dst,str((i+1)%7)))
        trains_list = list(ptr.fetchall())
        result += trains_list
    return result