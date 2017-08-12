import cv2
import numpy as np
import datetime
import re
import pytesseract
import logging
from PIL import Image
from scipy import ndimage

MONTH = {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12,
    }

class Finday(object):
    
    def __init__(self, directory):
        self.directory = directory
    
    def getDayFromImg(self,imagepath,fromY, arrPixel): #input image like amazon.png, Y_max of size chart (not size of image), arrPixel 
        self.arrPixel = arrPixel
        image = cv2.imread(imagepath)
        image = image[fromY+5:999,0:900]
        cv2.imwrite(self.directory +'/cutBotom.png',image)
        height,width = image.shape[:2]
        #zoom x3
        image = cv2.resize(image,(3*width, 3*height), interpolation = cv2.INTER_CUBIC)
        angle = -45
        #rotate -45
        image = ndimage.rotate(image, angle)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bitwise_not(gray)
        thresh = cv2.threshold(gray, 0, 255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        cv2.imwrite(self.directory+'/rolate.png',thresh)
        #find string from image
        _string = pytesseract.image_to_string(Image.open(self.directory+'/rolate.png'))
        self.arr = _string.split('\n')
        self.arr = list(filter(None,self.arr))
        logging.debug(self.directory+' cut day from image:{}'.format(self.arr))
        #example arr['May 2016', 'Jul 2016', 'Sep 2016', 'Nov 2016', 'Jan 2017', 'Mar 2017', 'May 2017', 'Jul 2017']
        self.findStyle() #1
        self.AutoSkip() #2
        self.findStep() #3
        if self.AutoCorrect():
            logging.debug(self.directory+' -----Correct')
        else:
            self.style = 'unknow'
            logging.debug(self.directory+' -----WRONG')
            return []
        if self.style == 'month-day':
            return [str(i.day)+'-'+str(i.month) for i in self.arrTime]
        elif self.style == 'year-month' or self.style == 'month':
            return [str(i.month)+'-'+str(i.year) for i in self.arrTime]
        elif self.style == 'hour-minute-second':
            return self.arr

    def findStyle(self): #return 'month-day' or 'hour-minute-second' or 'month-year' per Value 
        predictStyle = []
        today = datetime.date.today() # [year/mouth/day]
        for i,item in enumerate(self.arr):
            #B -> 8, | -> l, because "B" look like "8", "|" look like "l".
            self.arr[i] = item.replace('B','8')
            self.arr[i] = item.replace('|','l')
            match = re.match(r"([a-z]+)([0-9]+)", item.replace(' ',''), re.I)
            _style = 'unknow' #default 
            if not match:
                #case: Keepa return ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Ma', 'May', 'Jun', 'Jul', 'Aug']
                if len(item) == 3:
                    try:
                        _style = 'month'
                        self.arr[i] = MONTH[item]
                    except KeyError:
                        pass
                #fix case: keepa return ['11:20:00','13:20:00','15:20:00','17:20:00','19:20:00','21:20:00','23:20:00']
                elif ':' in item:
                    _style = 'hour-minute-second'
            else:
                _month,_num = match.groups()
                if len(_month) == 3:
                    if len(_num) == 4 and int(_num) in range(2000,2030):
                        try:
                            #case arr['May 2016', 'Jul 2016', 'Sep 2016', 'Nov 2016', 'Jan 2017', 'Mar 2017', 'May 2017', 'Jul 2017']
                            _style = 'year-month'
                            self.arr[i] = (int(_num),MONTH[_month])
                        except KeyError:
                            pass
                    elif int(_num) in range(1,32):
                        try:
                            #case normal arr[May 24]
                            _style = 'month-day'
                            self.arr[i] = (MONTH[_month], int(_num))
                        except KeyError:
                            pass
            predictStyle.append(_style)
        self.style = max(predictStyle,key=predictStyle.count)
        logging.debug(self.directory+' style: {}'.format(self.style))
        
    def AutoSkip(self): #convert to datetime.date(2017, 5, 16)
        today = datetime.date.today() # [year/mouth/day]
        self.arrTime = []
        for item in self.arr:
            d = today.day #default
            y = today.year
            m = today.month
            if self.style == 'month-day':
                if item[0] in range(1,13) and item[1] in range(1,32):
                    m,d = item
                else:
                    logging.debug(self.directory+' Skip:{}'.format(item))
                    self.arrTime.append('skip')
            elif self.style == 'year-month':
                if item[0] in range(2000,2030) and item[1] in range(1,13):
                    y,m = item
                else:
                    logging.debug(self.directory+' Skip:{}'.format(item))
                    self.arrTime.append('skip')
            elif self.style == 'hour-minute-second':
                pass
            elif self.style == 'month':
                if item in range(1,13):
                    if item > today.month: # month > current
                        y = y - 1 
                    m = item
                else:
                    logging.debug(self.directory+' Skip:{}'.format(item))
                    self.arrTime.append('skip')
            self.arrTime.append(datetime.date(y,m,d))
        
    def findStep(self):
        arr = self.arrTime
        if self.style == 'month-day':
            j = 0
            while arr[j] != 'skip' and arr[j+1] != 'skip':
                self.step = arr[j+1] - arr[j]  #unit is day
                logging.debug(self.directory+' step: {} days'.format(self.step.days))
                return
        elif self.style == 'year-month' or self.style == 'month':
            j = 0
            while arr[j] != 'skip' and arr[j+1] != 'skip':
                t_big = arr[j+1]
                t_small = arr[j]
                self.step = (t_big.month - t_small.month) + 12*(t_big.year-t_small.year) #unit is month
                logging.debug(self.directory+' step: {} month'.format(self.step))
                return
        elif self.style == 'hour-minute-second':
            return

    def AutoCorrect(self):
        if self.style == 'month-day':
            current = self.arrTime[0] #default arr[0] correct
            if current == 'skip':
                return False
            for i,item in enumerate(self.arrTime):
                if item == 'skip':
                    item = current
                    self.arrTime[i] = current
                _delta = current - item
                if _delta.days > 1:
                    return False
                current = item
                current = current + datetime.timedelta(days=self.step.days)
            return True
        elif self.style == 'year-month' or self.style == 'month':
            current = self.arrTime[0] #default arr[0] correct
            if current == 'skip':
                return False
            for i,item in enumerate(self.arrTime):
                if item == 'skip':
                    item = current
                    self.arrTime[i] = current
                if current != item:
                    return False
                #current = current + step
                m_current = current.month
                y_current = current.year
                d_current = current.day
                if m_current + self.step > 12:
                    y_current = y_current + 1
                    m_current = m_current + self.step - 12
                else:
                    m_current = m_current + self.step
                current = datetime.date(y_current,m_current,d_current)
            return True
        elif self.style == 'hour-minute-second':
            return True

    def getConst(self): #return O(x)-pixel, day per pixel
        if self.style == 'hour-minute-second' or self.style=='unknow':
            return None, None, None
        #style: month day
        lenghtTime = len(self.arrTime)
        lenghtPixel = len(self.arrPixel)
        
        if lenghtPixel - lenghtTime == 2:
            ##case 1
            # arrTime[0] -> arrPixel[1]
            # arrTime[-1] -> arrPixel[-2]
            Delta = self.arrTime[-1] - self.arrTime[0]
            self.DayPerPixel = Delta.days / (self.arrPixel[-2]-self.arrPixel[1])
            logging.debug(self.directory+' Case normal: 1{},{},{}'.format(self.arrTime[0],self.arrPixel[1],self.DayPerPixel))
            return self.arrTime[0], self.arrPixel[1], self.DayPerPixel
        elif lenghtPixel - lenghtTime == 1:
            ##case 2
            # arrTime[0] -> arrPixel[1]
            # arrTime[-1] -> arrPixel[-1]
            Delta = self.arrTime[-1] - self.arrTime[0]
            self.DayPerPixel = Delta.days / (self.arrPixel[-1]-self.arrPixel[1])
            logging.debug(self.directory+' Case 2: 1{},{},{}'.format(self.arrTime[0], self.arrPixel[1], self.DayPerPixel))
            return self.arrTime[0], self.arrPixel[1], self.DayPerPixel
        elif lenghtPixel - lenghtTime == 0:
            ##case 3
            # arrTime[0] -> arrPixel[0]
            # arrTime[-1] -> arrPixel[-1]
            Delta = self.arrTime[-1] - self.arrTime[0]
            self.DayPerPixel = Delta.days / (self.arrPixel[-1]-self.arrPixel[0])
            logging.debug(self.directory+' Case 3: 1{},{},{}'.format(self.arrTime[0], self.arrPixel[0], self.DayPerPixel))
            return self.arrTime[0], self.arrPixel[0], self.DayPerPixel