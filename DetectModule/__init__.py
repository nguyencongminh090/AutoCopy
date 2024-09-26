import cv2
import numpy as np
import utils


def detectBoard(img, top=0, left=0, enableBorder=False, rectangle=False):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)  

    thresh1 = cv2.bitwise_not(thresh.copy())

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    img1 = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    thresh = cv2.bitwise_and(thresh1, thresh1, mask=img1)
    

    if enableBorder:
        blurFilter = cv2.GaussianBlur(thresh, (3, 3), 0)
        circles = cv2.HoughCircles(blurFilter, cv2.HOUGH_GRADIENT, 1, 20, param1=300, param2=20, minRadius=10, maxRadius=30)

        maxR = 0
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                if i[2] > maxR:
                    maxR = i[2]
                cv2.circle(thresh, (i[0], i[1]), maxR + 2, (0, 0, 0), -1)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    minArea = 0
    curInfo = None, None, None, None

    contours = list(contours)

    contourGroup = utils.groupOverlappingContours(contours)

    for contour in contourGroup:
        area = cv2.contourArea(contour)
        contourPoly = cv2.approxPolyDP(contour, 4, True)
        boundRect = cv2.boundingRect(contourPoly)
        x1 = int(boundRect[0])
        y1 = int(boundRect[1])
        w = int(boundRect[2])
        h = int(boundRect[3])
            
        value = float(w) / h
        if (area > minArea) and (rectangle or 0.9 <= value <= 1.1):
            minArea = area
            curInfo = (x1 + left, y1 + top, w, h)
    return curInfo


def detectCircle(img, pos, sizeX, sizeY):
    x1, y1, w, h = pos
    rect = (x1, y1, x1 + w, y1 + h)

    disX = w / (sizeX - 1)
    disY = h / (sizeY - 1)

    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1, 20, param1=200, param2=20, minRadius=10, maxRadius=30)
    if circles is not None:
        circles = np.uint16(np.around(circles))
        listMove = utils.ArrangedArr()
        for c in circles[0, :]:
            x, y = c[0], c[1]
            if utils.isInside((x, y), rect):
                mask = np.zeros_like(img)
                cv2.circle(mask, (c[0], c[1]), c[2], (255, 255, 255), -1)
                meanVal = cv2.mean(img, mask=mask)[0]
                name = f'{chr(97 + int(np.around((x - x1) / disX)))}{15 - int(round((y - y1) / disY))}'
                if meanVal < 128:
                    listMove.add(name, 'b')
                else:
                    listMove.add(name, 'w')
        return listMove.get()
    return None