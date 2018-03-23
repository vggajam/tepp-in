import datetime as dt
import json

import requests

from db_tools import inter_stns, trains_btw_with_times, weekdays

fpass = ['51029','52963','52964','52973','52974','52975','52976','55337','55527','55528','56277','56278','56281','56282','56324','56921','56922','56925','56926','57625','57626','58433','58434','59204','59211','59212']
class_codes = ['1A','2A','3A','FC','CC','SL','2S']
def is_no_res(train_no):
    train_no = str(train_no)
    print(train_no)
    if train_no[0] != '5':
        return False
    if (train_no[0] == '5' and train_no is fpass):
        return False
    return False
def seat_check(trainno, src, dest, date, apikey, cla):
    if is_no_res(trainno):
        return 'NO-RES'
    result = 'NA-'
    seat_check_url = 'https://api.railwayapi.com/v2/check-seat/train/<train number>/source/<stn code>/dest/<dest code>/date/<dd-mm-yyyy>/pref/<class code>/quota/<quota code>/apikey/<apikey>/'
    quota = 'GN'
    url = seat_check_url.replace('<train number>', trainno).replace('<stn code>', src).replace('<dest code>', dest).replace('<dd-mm-yyyy>', date).replace('<quota code>', quota).replace('<apikey>', apikey).replace('<class code>', cla)
    print(url)
    for i in range(10):
        try:
            res = json.loads(requests.get(url).content)
            if str(res['response_code']) == '200':
                # print(res['availability'])
                for avail in res['availability']:
                    # print(date)
                    # print(str(avail['date']))
                    # print(str(avail['status']))    
                    if str(avail['date']) == date:
                        return str(avail['status'])
            else:
                return result+str(res['response_code'])
        except Exception as err:
            print(i, err)# pylint: disable=E1601
        if result != 404:
            return result+'404'
	return result+'404'

def get_trains_pair(src, intr, dst, jdate, db):
    #print('get_trainpair',src,intr,dst,week_day)# pylint: disable=E1601
    week_day = jdate.weekday()
    list1 = trains_btw_with_times(src, intr, week_day, db)
    if len(list1) <= 0:
        #print('no train btw',src, intr)# pylint: disable=E1601
        return None 
    # #print(list1[0])# pylint: disable=E1601
    week_day_2 = -1
    second_list = dict()
    list2 = None

    train_pairs =dict()
    for tpl in list1:
        second_train_day = (week_day + tpl[-1] - tpl[-2])%7
        for offset in range(2):
            week_day_2 = (second_train_day +offset)%7
            if week_day_2 not in second_list:
                second_list[week_day_2] = trains_btw_with_times(intr,dst,int(week_day_2),db)
            list2 = second_list[week_day_2]
            if list2 is None or len(list2) <= 0:
                #print('no train btw',intr, dst)# pylint: disable=E1601
                continue
            for tpl2 in list2:
                if tpl[0] == tpl2[0] or str(tpl[0])+'_'+str(tpl2[0]) in train_pairs or (offset ==0 and tpl[-4] < tpl[-3] and tpl2[4] <= tpl[5]):
                    continue
                train_pairs[str(tpl[0])+'_'+str(tpl2[0])]=[[tpl,week_day],[tpl2,week_day_2]]
    
    if train_pairs is None or len(train_pairs) <=0:
        print('No train pairs possible')# pylint: disable=E1601
        return None
    
    result_list = list()
    # cache = dict()
    #print(len(train_pairs))# pylint: disable=E1601
    for key in train_pairs:
        #trains.train_no,src.hop_index,dst.hop_index, src.arr_time, src.dept_time, dst.arr_time, dst.dept_time, src.day, dst.day from (hops as src inner join hops as dst on src.train_no = dst.train_no inner join trains on src.train_no = trains.train_no) where src.hop_index < dst.hop_index and src.stn_code = %s and dst.stn_code = %s and trains.%w = 1 and src.day = %s"
        pair = dict()
        json_pkt = dict()
        json_pkt['train_no'] = train_pairs[key][0][0][0]
        json_pkt['src'] = src
        json_pkt['dst'] = intr
        # json_pkt['sat'] = train_pairs[key][0][0][3]
        json_pkt['sdt'] = str(jdate+dt.timedelta(days=(train_pairs[key][0][1]-week_day+7)%7)+train_pairs[key][0][0][4])
        json_pkt['dat'] = str(jdate+dt.timedelta(days=(train_pairs[key][0][1]-week_day+7)%7)+train_pairs[key][0][0][5])
        time1 = jdate+dt.timedelta(days=(train_pairs[key][0][1]-week_day+7)%7)+train_pairs[key][0][0][5]
        # json_pkt['seat'] = seat_check(json_pkt['train_no'],json_pkt['src'],json_pkt['dst'], )
        # json_pkt['ddt'] = train_pairs[key][0][0][6]
        pair[0]=dict(json_pkt)
        
        json_pkt['train_no'] = train_pairs[key][1][0][0]
        json_pkt['src'] = intr
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
        result_list.append(dict(pair))
        # #print('')# pylint: disable=E1601
    result_list = sorted(result_list , key= lambda pair: dt.datetime.strptime(pair[1]['dat'], "%Y-%m-%d %H:%M:%S"))
    return result_list

def get_direct_trains(src, dst, jdate, db):
    week_day = jdate.weekday()
    direct_trains = trains_btw_with_times(src, dst, week_day, db)
    if direct_trains is None or len(direct_trains) <=0:
        return None
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
    
    res = sorted(res,key= lambda train: dt.datetime.strptime(train['dat'], "%Y-%m-%d %H:%M:%S"))
    return list(res)

def get_paths(src, dst, jdate, db, OnlyDirect=False):
    #print('get_paths',src,dst,jdate)# pylint: disable=E1601
    
    result = dict()

    direct_trains = get_direct_trains(src, dst, jdate, db)
    if direct_trains is not None and len(direct_trains) >0:
        result['direct'] = direct_trains
    result['direct'] = result['direct']
    if OnlyDirect:
        return result
    
    week_day = jdate.weekday()
    stns_list,_ = inter_stns(src, dst, week_day, db)
    if stns_list is None or len(stns_list) <=0:
        #print('no intermediate stations',src,dst)# pylint: disable=E1601
        return result
    
    stns_list = stns_list[:max([int(len(stns_list)/10), min([10,len(stns_list)])])] #top stations only
    # #print(stns_list)
    
    result['one_stop'] = list()
    for intr in stns_list:
        # print(intr)
        train_pairs = get_trains_pair(src,intr[0],dst,jdate, db)
        if train_pairs is not None:
            result['one_stop'] += train_pairs
    #2018-03-05 11:40:00
    result['one_stop'] = result['one_stop']
    return result


# import MySQLdb
# def connect_local():
#     db_details = json.load(open('./mysql_details.json'))
#     return MySQLdb.connect(host=db_details['host'],user = db_details['user'], port=db_details['port'],passwd=db_details['passwd'],db=db_details['db'])

# from db_tools import connect_local
# json.dump(get_paths('MUGR', 'SC',dt.datetime(2018,3,6),connect_local()), open('./op.json','w'))
# #print(trains_btw('MAS','BZJ','SUN'))
