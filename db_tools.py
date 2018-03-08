"""
    mysql tools
"""
import os
import json

import MySQLdb

def connect_local():
    db_details = json.load(open('./mysql_details.json'))
    return MySQLdb.connect(host=db_details['host'],user = db_details['user'], port=db_details['port'],passwd=db_details['passwd'],db=db_details['db'])

def connect_to_aws():
    db_details = json.load(open('./mysql-aws.json'))
    return MySQLdb.connect(host=db_details['host'],user = db_details['user'], port=db_details['port'],passwd=db_details['passwd'],db=db_details['db'])

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

inter_stns_query = """ select stations.stn_code, stations.trains_cnt from hops inner join stations on hops.stn_code = stations.stn_code where train_no = %s and hop_index > 0+%s and hop_index < 0+%s """
def inter_stns(src, dst, weekday, db):
    
    weekday,_ = week_day_code(weekday)
    if weekday is None:
        return None, None
    trains = trains_btw_with_times(src, dst, weekday, db)
    # print(trains)# pylint: disable=E1601
    if trains is None:
        print('No trains btw',src,dst)# pylint: disable=E1601
        return None,None
    stns_list = dict()
    ptr = db.cursor()
    for tpl in trains:
        # print((tpl[0],int(tpl[1]),int(tpl[2])))
        ptr.execute(inter_stns_query,(tpl[0],tpl[1],tpl[2]))
        for row in ptr:
            stns_list[row[0]]=int(row[1])
    # print(stns_list)
    stns_list_sorted = sorted(list(stns_list.items()), key = lambda x: x[1], reverse=True)
    # print(stns_list_sorted)
    return stns_list_sorted,trains

# inter_stns_query = """ select stations.stn_code, stations.trains_cnt from hops inner join stations on hops.stn_code = stations.stn_code where train_no = %s and hop_index > 0+%s and hop_index < 0+%s """
# def inter_stns(src, dst, weekday, db):
#     weekday = week_day_code(weekday)
#     if weekday is None:
#         return None, None;
#     trains = trains_btw_with_times(src, dst, weekday, db)
#     # print(trains)# pylint: disable=E1601
#     if trains is None:
#         print('No trains btw',src,dst)# pylint: disable=E1601
#         return None,None
#     stns_list = dict()
#     ptr = db.cursor()
#     for tpl in trains:
#         # print((tpl[0],int(tpl[1]),int(tpl[2])))
#         ptr.execute(inter_stns_query,(tpl[0],tpl[1],tpl[2]))
#         for row in ptr:
#             stns_list[row[0]]=int(row[1])
#     # print(stns_list)
#     stns_list_sorted = sorted(list(stns_list.items()), key = lambda x: x[1], reverse=True)
#     # print(stns_list_sorted)
#     return stns_list_sorted,trains

# reachable_stns_qry = """select distinct stations.stn_code, stations.trains_cnt from hops as hp inner join (select hops.train_no as tr, hops.stn_code as st,hops.hop_index as src_idx from hops where hops.stn_code = %s) as tb on hp.train_no= tb.tr, stations  where hp.hop_index > tb.src_idx  and stations.stn_code = hp.stn_code and trains_cnt > 39 order by trains_cnt desc;"""

# def reachable_stns(src, db):
#     ptr = db.cursor()
#     ptr.execute(reachable_stns_qry,(src)) 
#     stns = list(ptr.fetchall())
#     return stns

trains_btw_with_times_qry = "select trains.train_no,src.hop_index,dst.hop_index, src.arr_time, src.dept_time, dst.arr_time, dst.dept_time, src.day, dst.day from (hops as src inner join hops as dst on src.train_no = dst.train_no inner join trains on src.train_no = trains.train_no) where src.hop_index < dst.hop_index and src.stn_code = %s and dst.stn_code = %s and trains.%w = 1 and src.day = %s"
def trains_btw_with_times(src, dst, weekday, db):
    # log.write('trains_btw_with_times '+src+' '+dst+' '+str(weekday)+'\n')
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
        # log.write(qry+' '+src+' '+dst+' '+str((i+1)%7)+'\nrows returned = '+str(len(trains_list))+'\n')
    return result
# insert_station_query = """ INSERT INTO `train_enquiry_plus_plus`.`stations` (`stn_code`, `stn_name`) VALUES (%s, %s); """
# insert_train_query = """INSERT INTO `train_enquiry_plus_plus`.`trains` (`train_no`, `train_name`, `src_stn_code`, `dest_stn_code`, `MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`, `SUN`) VALUES (%s, %s, %s, %s, %s,%s,%s,%s,%s,%s,%s)"""
# insert_hop_query = """INSERT INTO `train_enquiry_plus_plus`.`hops` (`train_no`, `stn_code`, `arr_time`, `dept_time`, `hop_index`, `day`) VALUES (%s, %s, %s, %s, %s, %s);"""
# def insert_into_db_from_csv(qry,csv_path):
#     table = list()
#     for row in csv.reader(open(csv_path)):
#         if len(table) >0 and row[0] == table[-1][0] and row[1] == table[-1][1]:
#             print(row[0],row[1],'ignored')# pylint: disable=E1601
#             continue
#         table.append(tuple(row))
#     ptr = db.cursor()
#     ptr.executemany(qry, table)
#     db.commit()
#     print("rows inserted:",len(table))# pylint: disable=E1601

# def insert_stations_into_db(stations_list):
#     for station in stations_list:
#         ptr = db.cursor()
#         try:
#             ptr.execute(insert_station_query,(str(station),''))
#             db.commit()
#         except Exception as info:
#             print(info)# pylint: disable=E1601

# def get_stations_from_hops_csv(hops_csv_path):
#     stations = set()
#     for row in csv.reader(open(hops_csv_path)):
#         stations.add(str(row[1]).strip())
#     return list(stations)

# station_with_trains_cnt_qry = 'SELECT stn_code,count(*) FROM train_enquiry_plus_plus.hops group by stn_code'
# trains_cnt_update_qry ='UPDATE `train_enquiry_plus_plus`.`stations` SET `trains_cnt`=%s WHERE `stn_code`=%s'
# def update_trains_cnt():
#     ptr = db.cursor()
#     ptr.execute(station_with_trains_cnt_qry)
#     results = ptr.fetchall()
#     for row in results:
#         ptr.execute(trains_cnt_update_qry,(row[1],row[0]))
#     db.commit()
#     print(len(results),'rows updated')# pylint: disable=E1601


# trains_btw_query ={
#                     'MON':""" select trains.train_no,src.hop_index,dst.hop_index from (hops as src inner join hops as dst on src.train_no = dst.train_no inner join trains on src.train_no = trains.train_no) where src.hop_index < dst.hop_index and src.stn_code = %s and dst.stn_code = %s and trains.MON = 1 """,
#                     'TUE':""" select trains.train_no,src.hop_index,dst.hop_index from (hops as src inner join hops as dst on src.train_no = dst.train_no inner join trains on src.train_no = trains.train_no) where src.hop_index < dst.hop_index and src.stn_code = %s and dst.stn_code = %s and trains.TUE = 1 """,
#                     'WED':""" select trains.train_no,src.hop_index,dst.hop_index from (hops as src inner join hops as dst on src.train_no = dst.train_no inner join trains on src.train_no = trains.train_no) where src.hop_index < dst.hop_index and src.stn_code = %s and dst.stn_code = %s and trains.WED = 1 """,
#                     'THU':""" select trains.train_no,src.hop_index,dst.hop_index from (hops as src inner join hops as dst on src.train_no = dst.train_no inner join trains on src.train_no = trains.train_no) where src.hop_index < dst.hop_index and src.stn_code = %s and dst.stn_code = %s and trains.THU = 1 """,
#                     'FRI':""" select trains.train_no,src.hop_index,dst.hop_index from (hops as src inner join hops as dst on src.train_no = dst.train_no inner join trains on src.train_no = trains.train_no) where src.hop_index < dst.hop_index and src.stn_code = %s and dst.stn_code = %s and trains.FRI = 1 """,
#                     'SAT':""" select trains.train_no,src.hop_index,dst.hop_index from (hops as src inner join hops as dst on src.train_no = dst.train_no inner join trains on src.train_no = trains.train_no) where src.hop_index < dst.hop_index and src.stn_code = %s and dst.stn_code = %s and trains.SAT = 1 """,
#                     'SUN':""" select trains.train_no,src.hop_index,dst.hop_index from (hops as src inner join hops as dst on src.train_no = dst.train_no inner join trains on src.train_no = trains.train_no) where src.hop_index < dst.hop_index and src.stn_code = %s and dst.stn_code = %s and trains.SUN = 1 """,
#                 }
# def trains_btw(src, dst, weekday):
#     ptr = db.cursor()
#     if weekday not in trains_btw_query:
#         print('invalid weekday')# pylint: disable=E1601
#         return None
#     ptr.execute(trains_btw_query[weekday],(src,dst))
#     return ptr.fetchall()
# import csv
# db = connect_to_aws()
# qry = """UPDATE `trains` SET `MON`=%s, `TUE`=%s, `WED`=%s, `THU`=%s, `FRI`=%s, `SAT`=%s, `SUN`=%s WHERE `train_no`=%s;"""
# def update_table():
#     rd = csv.reader(open('./trains.csv'))
#     head_row = next(rd)
#     print(head_row)
#     ptr = db.cursor()
#     for row in rd:
#         tpl = (row[4], row[5], row[6],row[7], row[8], row[9],row[10],row[0])
#         # print(tpl)
#         # return;
#         ptr.execute(qry,tpl)
#         ptr.fetchall()
#     db.commit()

# update_table()