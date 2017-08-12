import cv2
import numpy as np
import logging

from FindNumbers import FindNumber
from FindPixels import FindPixel
from GetKeepa import getImageKeepa
from FindDays import Finday


class Keepa(object):
    
    def __init__(self, directory):
        self.directory = directory

    def keepa(self,Asin,Amazon=True,Salesrank=False):
        if Amazon:
            imgPath = self.directory +'/amazon.png'
            imTempPath = self.directory +'/amztemp.png'
            getImageKeepa(imgPath,Asin,Amazon=1,Salesanks=0,Range=90,cFont='ffffff')
            getImageKeepa(imTempPath,Asin,Amazon=1,Salesanks=0,Range=90,cFont='000000')
        if Salesrank:
            imgPath = self.directory +'/salerank.png'
            imTempPath = self.directory +'/saletemp.png'
            getImageKeepa(imgPath,Asin,Amazon=0,Salesanks=1,Range=90,cFont='ffffff')
            getImageKeepa(imTempPath,Asin,Amazon=0,Salesanks=1,Range=90,cFont='000000')
            
        img1 = cv2.imread(imgPath,0)
        img2 = cv2.imread(imTempPath)

        number = FindNumber(self.directory)
        WIDTH, HEIGHT = number.findBorder(img1)

        if WIDTH[1] == 48 or HEIGHT[1]==500:
            logging.debug(self.directory+' Sorry, no history data found.')
            return False

        logging.debug(self.directory+' width:{}, height:{}'.format(WIDTH,HEIGHT))
        self.x_min, self.x_max = WIDTH
        self.y_min, self.y_max = HEIGHT

        if Amazon:
            #max min of column
            #price per pixel and ranks per pixel
            self.prices = number.GetPrices(img1)
            self.PriceMax = self.prices[-1][1]
            self.PriceMin = self.prices[0][1]
            self.PricePerPixel = (self.PriceMax - self.PriceMin)/(self.y_max-self.y_min)
            self.posCol = number.getPosCol()

        if Salesrank:
            self.ranks = number.GetRanks(img1)
            self.RankMax = self.ranks[-1][1]
            self.RankMin = self.ranks[0][1]
            self.RankPerPixel = (self.RankMax - self.RankMin)/(self.y_max-self.y_min)
            self.posCol = number.getPosCol()

        Day = Finday(self.directory)
        self.days = Day.getDayFromImg(imgPath,self.y_max,self.posCol)
        logging.debug(self.directory+' Auto correct days: {}'.format(self.days))
        self.timeZero ,self.pixelTimeZero ,self.DayPerPixel = Day.getConst()

        Element = FindPixel()
        self.result = Element.GetPixelNonZero(img2, self.x_min, self.y_min, self.x_max, self.y_max)
        return True
    
    def FindRankY(self,pointY): #input pointY -> Rank at Y
        return self.RankMax-(pointY-self.y_min)*self.RankPerPixel

    def FindPriceY(self,pointY):#input pointY -> Price at Y
        return self.PriceMax-(pointY-self.y_min)*self.PricePerPixel

    def FindRankX(self,pointX): #input pointX -> Rank at X
        try:
            pointY = self.result[pointX]
            return round(self.FindRankY(pointY),0)
        except KeyError:
            logging.debug(self.directory+' x:{} not exist'.format(pointX))
            return -1

    def FindPriceX(self,pointX): #input pointX -> Price at X
        try:
            pointY = self.result[pointX]
            return round(self.FindPriceY(pointY),2)
        except KeyError:
            logging.debug(self.directory+' x:{} not exist'.format(pointX))
            return -1

    def FindAvgPrice(self):
        # find avg pixel-y
        total = 0
        for item in self.result:
            total = total + self.result[item]
        try:
            YpixelAvg = int(total/len(self.result))
            return round(self.FindPriceY(YpixelAvg),2)
        except ZeroDivisionError:
            return -1

    def FindAvgRank(self):
        total = 0
        for item in self.result:
            total = total + self.result[item]
        try:
            YpixelAvg = int(total/len(self.result))
            return round(self.FindRankY(YpixelAvg),2)
        except ZeroDivisionError:
            return -1
        
    def FindPriceDay(self, time):
        try:
            Delta = time - self.timeZero
            x = int(Delta.days/self.DayPerPixel + self.pixelTimeZero)
            return self.FindPriceX(x)
        except TypeError:
            pass

    def FindRankDay(self, time):
        try:
            Delta = time - self.timeZero
            x = int(Delta.days/self.DayPerPixel + self.pixelTimeZero)
            return self.FindRankX(x)
        except TypeError:
            pass

    def RewriteImage(self,imgRewrite ,Amazon=True,Salesrank=False):
        #step 1 draw map
        for key in self.result:
            try:
                y = self.result[key]
                x = key
                ypre = self.result[key-1]
                xpre = key - 1
                if Amazon:
                    cv2.line(imgRewrite,(xpre,ypre),(x,y),(0,0,255),1)
                if Salesrank:
                    cv2.line(imgRewrite,(xpre,ypre),(x,y),(255,0,0),1)
            except KeyError:
                pass
        #step 2 draw number column
        if Amazon:
            for y,price in self.prices:
                cv2.putText(imgRewrite, str(price), (self.x_min-30, y+20),cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0), 1)
            
        if Salesrank:
            for y,rank in self.ranks:
                cv2.putText(imgRewrite, str(rank), (self.x_max+30, y),cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0), 1)
            
        return imgRewrite

    def drawCol(self,imgRewrite):
        cols = self.posCol
        cv2.line(imgRewrite,(cols[0],self.y_max),(cols[0],self.y_max-15),(255,255,255),1)
        cv2.line(imgRewrite,(cols[-1],self.y_max),(cols[-1],self.y_max-15),(255,255,255),1)

        for i in range(0,len(self.days)):
            cv2.line(imgRewrite,(cols[i+1],self.y_max),(cols[i+1],self.y_max-15),(255,255,255),1)
            cv2.putText(imgRewrite, self.days[i], (cols[i+1], self.y_max+10),cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 255), 1)
        return imgRewrite

    def drawLineAtDay(self,imgRewrite,time,Amazon=True,Salesrank=False):
        try:
            Delta = time - self.timeZero
            x = int(Delta.days/self.DayPerPixel + self.pixelTimeZero)
            if Amazon:
                try:
                    cv2.line(imgRewrite,(x,self.y_max),(x,self.result[x]),(153, 0, 153),1)
                    cv2.line(imgRewrite,(x,self.result[x]),(self.x_min,self.result[x]),(153, 0, 153),1)
                except KeyError:
                    pass
            if Salesrank:
                try:
                    cv2.line(imgRewrite,(x,self.y_max),(x,self.result[x]),(204, 255, 51),1)
                    cv2.line(imgRewrite,(x,self.result[x]),(self.x_max,self.result[x]),(204, 255, 51),1)
                except KeyError:
                    pass
        except TypeError:
            pass
        return imgRewrite