import datetime
import argparse as ap
import numpy as np
import cv2
import os
import sys
import logging
from multiprocessing.dummy import Pool as ThreadPool
from KeepaChart import Keepa


#get image from keepa
parser = ap.ArgumentParser()
parser.add_argument("-a", "--asin", help="", required="True")
args = vars(parser.parse_args())
ASIN = args['asin']
logging.basicConfig(filename='log', level=logging.DEBUG, format='%(asctime)s [%(message)s] %(thread)d')

# request = True
directory = './data/' + ASIN
if not os.path.exists(directory):
    os.makedirs(directory)
    with open('./data/listasin.txt','a') as F:
        F.write(ASIN+'\n')
elif os.listdir(directory) != []:
    pass
    # request = False
logging.debug('------Begin task :{}'.format(ASIN))
print('------Begin task :{}'.format(ASIN))
t = datetime.date(2017,7,28)

try:
    A = Keepa(directory)
    complete_price = A.keepa(ASIN,True,False)
    if complete_price:
        # imgRe = np.zeros((1000,1000,3), np.uint8)
        logging.debug(directory+' price avg:{}'.format(A.FindAvgPrice()))
        # imgRe = A.RewriteImage(imgRe,Amazon=True,Salesrank=False)
        # imgRe = A.drawCol(imgRe)
        
        logging.debug(directory+' price day {}:{}'.format(t,A.FindPriceDay(t)))
        # imgRe = A.drawLineAtDay(imgRe,t,Amazon=True,Salesrank=False)
except IndexError:
    complete_price = False
try:
    B = Keepa(directory)
    complete_rank = B.keepa(ASIN,False,True)
    if complete_rank:
        # imgRa = np.zeros((1000,1000,3), np.uint8)
        logging.debug(directory+' rank avg:{}'.format(B.FindAvgRank()))
        # imgRa = B.RewriteImage(imgRa,Amazon=False,Salesrank=True)
        # imgRa = B.drawCol(imgRa)
        logging.debug(directory+' Rank day {}:{}'.format(t,B.FindRankDay(t)))
        # imgRa = B.drawLineAtDay(imgRa,t,Amazon=False,Salesrank=True)
except IndexError:
    complete_rank = False
logging.debug('------End task :{}'.format(ASIN))
print('------End task :{}'.format(ASIN))
# if complete_price:
#     cv2.imshow('price',cv2.resize(imgRe,(1000,600), interpolation = cv2.INTER_CUBIC))
# if complete_rank:
#     cv2.imshow('rank',cv2.resize(imgRa,(1000,600), interpolation = cv2.INTER_CUBIC))

# cv2.waitKey()

# second = datetime.datetime.now() - second
# logging.debug(directory+' total time:{}'.format(second.total_seconds()))