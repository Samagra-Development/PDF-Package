import os.path
import logging
import logging.config
import requests
import urllib
import json


def initialize_logger():
    """

    :return: logger object
    """
    log_file = os.path.dirname(__file__) + '/../utils/log.conf'
    logging.config.fileConfig(fname=log_file, disable_existing_loggers=False)
    return logging

def send_whatsapp_msg(mobile, url, name):
    headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/x-www-form-urlencoded',
               'apikey': 'c2ed3ece4e7c40eac0af0e012866e090', 'cache-control': 'no-cache'}
    message = {"type":"text","text":"Your resume is here => "+url}
    message = urllib.parse.quote(json.dumps(message))
    print(message)
    params = 'channel=whatsapp&source=917834811114&destination='+'91'+str(mobile)
    params +='&message='+message+'&src.name='+name
    result = requests.request("POST", 'https://api.gupshup.io/sm/api/v1/msg', data=params, headers=headers)
    print(result)
    error = None
    if result.status_code != 200:
        error = 'Unable to send msg'
        print(result.__dict__)
    return error

