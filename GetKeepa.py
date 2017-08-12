import urllib.request
import shutil
import logging
import os
import requests

def getImageKeepa(path, Asin,Amazon=1,Salesanks=0,Range=90,cFont='ffffff', New=0, Used=0):
    if os.path.isfile(path) and os.stat(path).st_size != 0:
        logging.debug('File {} exist'.format(path))
        return
    url_api = r'https://dyn.keepa.com/pricehistory.png?asin={}&domain=com&width=1000&height=1000&amazon={}&new={}&used={}&range={}&salesrank={}&cBackground=000000&cFont={}&cAmazon=ff0000&cNew=ff0000&cUsed=ff0000'.format(Asin,Amazon,New,Used,Range,Salesanks,cFont)
    
    response = requests.get(url_api,stream = True)
    if response.status_code == 200:
        logging.debug('URL API: {}'.format(url_api))
        print('URL API: {}'.format(path))
        with open(path, 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
        #file is empty
        if os.stat(path).st_size == 0:
            logging.debug('resend request: {}'.format(path))
            print('resend request: {}'.format(path))
            getImageKeepa(path, Asin,Amazon,Salesanks,Range,cFont, New, Used)
    else:
        logging.debug('request fail: {}'.format(path))
        print('request fail: {}'.format(path))
