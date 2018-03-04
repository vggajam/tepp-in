import datetime as dt
import json

from db_tools import inter_stns, trains_btw_with_times, weekdays
# connect_to_cloudsql()
# log = open('./tepp.log','w')
def get_trainspair(src, intr, dst, week_day, db):
    #print('get_trainpair',src,intr,dst,week_day)# pylint: disable=E1601
    list1 = trains_btw_with_times(src, intr, week_day, db)
    list1 = sorted(list1, key= lambda x:x[-1])
    if len(list1) <= 0:
        #print('no train btw',src, intr)# pylint: disable=E1601
        return None 
    # #print(list1[0])# pylint: disable=E1601
    week_day_2 = -1
    second_list = dict()
    list2 = None

    result_list =dict()
    for tpl in list1:
        second_train_day = (week_day + tpl[-1] - tpl[-2])%7
        for offset in range(3):
            week_day_2 = (second_train_day +offset)%7
            if week_day_2 not in second_list:
                second_list[week_day_2] = trains_btw_with_times(intr,dst,int(week_day_2),db)
            list2 = second_list[week_day_2]
            if list2 is None or len(list2) <= 0:
                #print('no train btw',intr, dst)# pylint: disable=E1601
                continue
            for tpl2 in list2:
                if tpl[0] == tpl2[0] or str(tpl[0])+'_'+str(tpl2[0]) in result_list or (offset ==0 and tpl[-4] < tpl[-3] and tpl2[4] <= tpl[5]):
                    continue
                result_list[str(tpl[0])+'_'+str(tpl2[0])]=[[tpl,week_day],[tpl2,week_day_2]]
    return result_list
    
def get_paths(src, dst, jdate, db, OnlyDirect=False):
    #print('get_paths',src,dst,jdate)# pylint: disable=E1601
    week_day = jdate.weekday()
    result = dict()
    
    stns_list,direct_trains = inter_stns(src, dst, week_day, db)
    res = list()
    for train in direct_trains:
        json_pkt = dict()
        json_pkt['train_no'] = train[0]
        json_pkt['src'] = src
        json_pkt['dst'] = dst
        json_pkt['sdt'] = str(jdate+train[4])
        # #print(train[-3])
        json_pkt['dat'] = str(jdate+train[5]+dt.timedelta(days=train[-1]-train[-2])-dt.timedelta(days=(int(train[-3]<train[-4])if train[-3] !=dt.timedelta(0) else 0)))
        res.append(dict(json_pkt))
    result['direct'] = list(res)
    if OnlyDirect:
        return result
    stns_list = stns_list[:max([int(len(stns_list)/10), min([10,len(stns_list)])])] #top stations only
    # #print(top_stns_list)
    if stns_list is None:
        #print('no intermediate stations',src,dst)# pylint: disable=E1601
        return result
    res = dict()
    for intr in stns_list:
        res[intr[0]]=list()# pylint: disable=E1601
        train_pairs = get_trainspair(src,intr[0],dst,week_day, db)
        if train_pairs is None:
            res[intr[0]] = None
            return res
        #print(len(train_pairs))# pylint: disable=E1601
        for key in train_pairs:
            #trains.train_no,src.hop_index,dst.hop_index, src.arr_time, src.dept_time, dst.arr_time, dst.dept_time, src.day, dst.day from (hops as src inner join hops as dst on src.train_no = dst.train_no inner join trains on src.train_no = trains.train_no) where src.hop_index < dst.hop_index and src.stn_code = %s and dst.stn_code = %s and trains.%w = 1 and src.day = %s"
            pair = dict()
            json_pkt = dict()
            json_pkt['train_no'] = train_pairs[key][0][0][0]
            json_pkt['src'] = src
            json_pkt['dst'] = intr[0]
            # json_pkt['sat'] = train_pairs[key][0][0][3]
            json_pkt['sdt'] = str(jdate+dt.timedelta(days=(train_pairs[key][0][1]-week_day+7)%7)+train_pairs[key][0][0][4])
            json_pkt['dat'] = str(jdate+dt.timedelta(days=(train_pairs[key][0][1]-week_day+7)%7)+train_pairs[key][0][0][5])
            time1 = jdate+dt.timedelta(days=(train_pairs[key][0][1]-week_day+7)%7)+train_pairs[key][0][0][5]
            
            # json_pkt['ddt'] = train_pairs[key][0][0][6]
            pair[0]=dict(json_pkt)
            
            json_pkt['train_no'] = train_pairs[key][1][0][0]
            json_pkt['src'] = intr[0]
            json_pkt['dst'] = dst
            # json_pkt['sat'] = train_pairs[key][0][0][3]
            json_pkt['sdt'] = str(jdate+dt.timedelta(days=(train_pairs[key][1][1]-week_day+7)%7)+train_pairs[key][1][0][4])
            time2 = jdate+dt.timedelta(days=(train_pairs[key][1][1]-week_day+7)%7)+train_pairs[key][1][0][4]
            json_pkt['dat'] = str(jdate+dt.timedelta(days=(train_pairs[key][1][1]-week_day+7)%7)+train_pairs[key][1][0][5])
            # json_pkt['ddt'] = train_pairs[key][0][0][6]
            pair[1] = dict(json_pkt)
            # #print(dt.datetime(pair[1]['sdt'])) #pylint: disable=E1601
            # #print(dt.datetime(pair[0]['dat'])) #pylint: disable=E1601
            if time2-time1 > dt.timedelta(hours=12) or time2-time1 < dt.timedelta(0):
                continue
            pair['wt'] = str(time2-time1)
            # #print(pair)
            res[intr[0]].append(dict(pair))
            # #print('')# pylint: disable=E1601
    result['one_stop'] = res
    # #print(result)
    # json.dump(result,open('./op.json','w'))
    return result
# get_paths('KZJ', 'MUGR',dt.datetime(2018,3,5),False)
# #print(trains_btw('MAS','BZJ','SUN'))
