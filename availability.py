import requests
import json

cache = dict()

apikey = json.load(open('./railapi.json'))['kvsk']

def seat_check(trainno,src,dest,date,cla, apikey):
	key = str(trainno)+'_'+str(src)+'_'+str(dest)+'_'+str(date)+'_'+str(cla)
	if key not in cache:
		cache[key] = 'NA'
		seat_check_url = 'https://api.railwayapi.com/v2/check-seat/train/<train number>/source/<stn code>/dest/<dest code>/date/<dd-mm-yyyy>/pref/<class code>/quota/<quota code>/apikey/<apikey>/'
		quota = 'GN'
		url = seat_check_url.replace('<train number>', trainno).replace('<stn code>', src).replace('<dest code>', dest).replace('<dd-mm-yyyy>', date).replace('<class code>', cla).replace('<quota code>', quota).replace('<apikey>', apikey)
		try:
			res = json.loads(requests.get(url).content)
			if res['response_code'] == 200:
				for avail in res['availability']:
					if avail['date'] == date:
						cache[key] = avail['status']
						break
		except Exception as err:
			print(key, err)# pylint: disable=E1601
			pass
	return cache[key]

print(seat_check('12709','OGL','KZJ','18-3-2018','SL',apikey))
