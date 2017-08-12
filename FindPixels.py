import cv2
import numpy as np
import operator
import logging


class FindPixel(object):

    def GetPixelNonZero(self, image, widthMin, heightMin, widthMax, heightMax): #input image normal
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # define range of blue color in HSV
        lower_blue = np.array([0,110,0])
        upper_blue = np.array([255,255,255])
        # Threshold the HSV image to get only blue colors
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        # Bitwise-AND mask and original image
        NonBackground = cv2.bitwise_and(image,image, mask= mask)
        gray = cv2.cvtColor(NonBackground, cv2.COLOR_BGR2GRAY)
        ret,thresh = cv2.threshold(gray,50,255, cv2.THRESH_BINARY)
        #numpy returns (row,col) = (y,x), and OpenCV returns (x,y) = (col,row)
        thresh[30:100,908:930] = 0 #delete rectangle green
        # cv2.imshow('im',thresh)
        # cv2.waitKey()
        Pixels = cv2.findNonZero(thresh)
        Pixels = FindPixel.convertTodict(Pixels)
        xfrom = widthMin
        # xmax = widthMax
        results = {}
        while 1:
            result,xCurrent = self.ConvertPixels(Pixels,xfrom, widthMax)
            if not result:
                break
            else:
                results.update(result)
            if xCurrent < widthMax:
                xfrom = xCurrent + 1
            else: 
                break
        return results

    def FindPointY(self,pointX,pixels): #find y from x in pixels
        try:
            return pixels[pointX]
        except KeyError:
            return []

    def FindxMin(self,pixels, xfrom, widthMax):
        xMin = xfrom
        _array = self.FindPointY(xMin, pixels)
        while not _array:
            xMin = xMin + 1
            _array = self.FindPointY(xMin, pixels)
            if xMin >= widthMax:
                return None, None
        if len(_array) > 1:
            logging.debug('Warning min X multiple value: {}'.format(xMin))
        return xMin ,_array

    def ConvertPixels(self,pixels,xfrom,widthMax):
        xCurrent, TempArray = self.FindxMin(pixels, xfrom,widthMax)
        try:
            yCurrent = TempArray[0]
            result = {xCurrent:yCurrent}
        except TypeError:
            return None, None

        done = False
        logging.debug('Head:{}'.format(xCurrent))
        while not done:
            if xCurrent > widthMax:
                done = True
            xCurrent = xCurrent + 1
            ArrayCurrent = self.FindPointY(xCurrent,pixels)
            if not ArrayCurrent: #return notthing
                if self.FindPointY(xCurrent+1,pixels):
                    #noise of border
                    result[xCurrent] = yCurrent
                    continue
                else:
                    done = True
                    break
            duplicate = FindPixel.CheckDuplicate(TempArray,ArrayCurrent)
            if duplicate:
                result[xCurrent] = yCurrent
            else:
                resY = FindPixel.SelectPointY(ArrayCurrent, yCurrent)
                if resY:
                    result[xCurrent] = resY
                    yCurrent = resY
                else:
                    result[xCurrent] = yCurrent
            TempArray = ArrayCurrent
            # logging.debug('select:{}'.format(yCurrent))
        logging.debug('Tail:{}'.format(xCurrent))
        return result, xCurrent
    
    @staticmethod
    def convertTodict(Pixels):
        results = {}
        for index in Pixels:
            try:
                #exist append
                results[index[0][0]].append(index[0][1])
            except KeyError:
                #ney key
                results[index[0][0]] = []
                results[index[0][0]].append(index[0][1])
        return results
    
    @staticmethod
    def SelectPointY(ArrayCurrent,yCurrent):
        head = False
        tail = False
        lenght = len(ArrayCurrent)
        try:
            index = ArrayCurrent.index(yCurrent)
        except ValueError:
            if yCurrent < ArrayCurrent[0]:
                return ArrayCurrent[0]
            else:
                return ArrayCurrent[-1]
        if abs((ArrayCurrent[-1]-ArrayCurrent[0]) - (lenght+1)) > 10:
            # print('Warning:this pixel noise')
            return None
        if index in range(0,3):
            head = True
        if index in range(lenght-3,lenght):
            tail = True
        if head and not tail:
            return ArrayCurrent[-1]
        if tail and not head:
            return ArrayCurrent[0]
        if not head and not tail:
            # logging.debug('Warning:ignore this pixel')
            return None
        return ArrayCurrent[int(lenght/2)]
    
    @staticmethod
    def CheckDuplicate(array1, array2):
        array1 = set(array1)
        array2 = set(array2)
        if abs(len(array2) - len(array1)) < 2:
            if array1.issubset(array2) or array2.issubset(array1):
                return True
        return False