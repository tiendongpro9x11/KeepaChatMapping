import cv2
import numpy as np
import NumberMatrix
import logging

class FindNumber(object):
    
    def __init__(self, directory):
        self.directory = directory
    
    #threshold = 0.88 # 88% matching
    def MatchNumber(self, image, threshold=0.85): #input image white-black
        templates = NumberMatrix.get_number()
        column = []
        text_drawed = {}
        keys = []
        #add all match to dict 
        for number in range(12):
            template = templates[number]
            if number >= 10:
                number -= 10    
            width, height = template.shape[::-1]
            #Apply template Matching
            result = cv2.matchTemplate(image,template,cv2.TM_CCOEFF_NORMED)
            loc = np.where(result >= threshold)
            for pt in zip(*loc[::-1]):
                top_left = pt
                bottom_right = (top_left[0] + width, top_left[1] + height)
                #find match number 0-9
                #concat number to price when y point every top_left[1] (y) equal
                try:
                    #if key exist
                    text_drawed[str(top_left[1])].append((top_left[0],top_left[1],number))
                except KeyError:
                    #new key
                    text_drawed[str(top_left[1])] = []
                    text_drawed[str(top_left[1])].append((top_left[0],top_left[1],number))
                    keys.append(str(top_left[1]))
        #concat macth to number if equal y
        for key in keys:
            _temp = sorted(set(text_drawed[key]))
            price = ''
            for item in _temp:
                price = price + str(item[2])
            column.append((int(key),int(price)))
        return column

    def CheckResult(self,column): #simple check. step = level 1 - level 0 = level 2 - level 1
        if len(column) < 2: #min of column equal 2
            return False
        #0 -> point-y, 1 -> price
        step = column[1][1] - column[0][1]
        price_current = column[0][1]
        
        for point,price in column[1:]:
            price_current = price_current + step
            if price_current != price:
                logging.debug(self.directory+" ERROR: Result wrong")
                return False
        return True

    def findBorder(self,image):
        #set default
        widthMin = 48
        heightMin = 36
        ########################
        widthMax = 48 #check from 800 faster
        thres = image[heightMin:heightMin+1,widthMax:widthMax+1]
        nextThres = image[heightMin:heightMin+1,widthMax+1:widthMax+2]
        self.indColumn = []
        while thres != [[0]] and nextThres != [[0]]:
            thresColumn = image[heightMin+2:heightMin+3,widthMax:widthMax+1]
            if thresColumn != [[0]]:
                self.indColumn.append(widthMax)
            widthMax = widthMax + 1
            thres = image[heightMin:heightMin+1,widthMax:widthMax+1]
            nextThres = image[heightMin:heightMin+1,widthMax+1:widthMax+2]
            
        ## find column of month index

        ##
        heightMax = 500 #check from 500 faster
        thres = image[heightMax:heightMax+1,widthMin:widthMin+1]
        nextThres = image[heightMax+1:heightMax+2,widthMin:widthMin+1]

        while thres != [[0]] and nextThres != [[0]]:
            heightMax = heightMax + 1
            thres = image[heightMax:heightMax+1,widthMin:widthMin+1]
            nextThres = image[heightMax+1:heightMax+2,widthMin:widthMin+1]

        self.widthMin = widthMin
        self.widthMax = widthMax
        self.heightMin = heightMin
        self.heightMax = heightMax

        return (widthMin,widthMax),(heightMin,heightMax)


    def GetPrices(self,image): #input image white-black
        #select left column
        #599 size of image
        ImageLeft = image[self.heightMin-10:999,0:self.widthMin]
        cv2.imwrite(self.directory + '/cutLeft.png',ImageLeft)
        price_column = self.MatchNumber(ImageLeft)
        logging.debug(self.directory+' prices:{}'.format(price_column))
        price_column = sorted(price_column, reverse=True)
        if self.CheckResult(price_column):
            return price_column
        logging.debug(self.directory+' Can not get price. Something wrong')
        return None
    
    def GetRanks(self,image): #input image white-black
        #select right column
        #999 size of image
        ImageRight = image[0:999,self.widthMax:999]
        cv2.imwrite(self.directory + '/cutRight.png',ImageRight)
        ranks_column = self.MatchNumber(ImageRight)
        #fix bug sales rank S ~ 5
        ranks_column.remove((36,5))
        #end fix
        logging.debug(self.directory+' ranks:{}'.format(ranks_column))
        ranks_column = sorted(ranks_column,reverse=True)
        if self.CheckResult(ranks_column):
            return ranks_column
        logging.debug(self.directory+' Can not get rank. Something wrong')
        return None

    def getPosCol(self):
        if len(self.indColumn) > 30:
            logging.debug(self.directory+' total column > 30')
            return []
        return self.indColumn