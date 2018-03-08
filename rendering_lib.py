import datetime as dt

from flask import render_template


def render_direct_trains_row(trains):
    res = ''
    for train in trains:
        res += render_template('direct_train_row.html',
                                train_no = train['train_no'],
                                src = train['src'],
                                dst = train['dst'],
                                sdt = train['sdt'],
                                dat = train['dat'])
    return res

def render_one_stop_row(trains):
    res = ''
    for train_pair in trains:
        # print(train_pair)
        res += render_template('one_stop_row.html',
                                train_no1=train_pair[0]['train_no'],
                                src1=train_pair[0]['src'],
                                sdt1=train_pair[0]['sdt'],
                                dst1=train_pair[0]['dst'],
                                dat1=train_pair[0]['dat'],
                                train_no2=train_pair[1]['train_no'],
                                src2=train_pair[1]['src'],
                                sdt2=train_pair[1]['sdt'],
                                dst2=train_pair[1]['dst'],
                                dat2=train_pair[1]['dat'],
                                wt=train_pair['wt'])
    return res
