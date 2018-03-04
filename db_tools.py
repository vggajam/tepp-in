"""
    mysql tools
"""

weekdays = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

inter_stns_query = """ select stations.stn_code, stations.trains_cnt from hops inner join stations on hops.stn_code = stations.stn_code where train_no = %s and hop_index > 0+%s and hop_index < 0+%s """
def inter_stns(src, dst, weekday, db):
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

trains_btw_with_times_qry = "select trains.train_no,src.hop_index,dst.hop_index, src.arr_time, src.dept_time, dst.arr_time, dst.dept_time, src.day, dst.day from (hops as src inner join hops as dst on src.train_no = dst.train_no inner join trains on src.train_no = trains.train_no) where src.hop_index < dst.hop_index and src.stn_code = %s and dst.stn_code = %s and trains.%w = 1 and src.day = %s"
def trains_btw_with_times(src, dst, weekday, db):
    # log.write('trains_btw_with_times '+src+' '+dst+' '+str(weekday)+'\n')
    week_day_no = 0
    if type(weekday) is type(0):
        if weekday<7 and weekday >=0 :
            # weekday = weekdays[weekday]
            week_day_no = weekday
        else:
            print('invalid weekday')# pylint: disable=E1601
            return None
    elif type(weekday) == type('MON'):
        try:
            week_day_no = weekdays.index(weekday)
        except ValueError as err:
            print('invalid weekday',err,weekday,week_day_no)# pylint: disable=E1601
            return None
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
