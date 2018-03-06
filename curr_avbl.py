import requests
import json
import time
import datetime as dt
from tepp import get_direct_trains
from db_tools import connect_local
from datetime import datetime
from twilio.rest import Client
from twilio.http.http_client import TwilioHttpClient

proxy_client = TwilioHttpClient()
# proxy_client.session.proxies = {'https': '172.30.0.13:3128'}
client = Client('ACee8fe684904df1bdf504445569670e3c', '2b7eef0c2b48c88a628d8c481e5b6d1b', http_client=proxy_client)

temp = 'https://api.railwayapi.com/v2/check-seat/train/<train number>/source/<stn code>/dest/<dest code>/date/<dd-mm-yyyy>/pref/<class code>/quota/<quota code>/apikey/<apikey>/'

def curr_avbl(src,dest,date,cla,phoneno):
	quota = 'GN'
	apikey = '13hsbmw7vg'

	db = connect_local()
	jdate=dt.datetime(int(date[2]),int(date[1]),int(date[0]))
	trains = get_direct_trains(src,dest,jdate,db)
	
	done = False
	while not done:
		remove = list()
		for each_train in trains:
			url = temp.replace('<train number>', each_train['train_no']).replace('<stn code>',src).replace('<dest code>',dest).replace('<dd-mm-yyyy>',date).replace('<class code>',cla).replace('<quota code>',quota).replace('<apikey>',apikey)

			res = requests.get(url).content
			res = json.loads(res)
			res = res['availability'][0]['status']
			
			message = each_train['train_no'] + " : " + str(datetime.now()) + " : " + res
			print(message)
			
			if "CURR" in res:
				client.api.account.messages.create(
					to = "+91" + phoneno,
					from_ = "+14064123367",
					body = message
				)
				print("message sent successfully!")
				done = True
				break

			elif res == "TRAIN DEPARTED":
				remove.append(each_train['train_no'])

		for each_train in remove:
			trains.remove(each_train)

		if len(trains) == 0:
			done = True

		time.sleep(1080)
		
