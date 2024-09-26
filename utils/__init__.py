import keyboard
from threading import Thread
import time
import ctypes
import mss
import numpy as np
import cv2
import tkinter as tk
from PIL import Image, ImageTk
import win32api, win32con
from DetectModule import detectBoard, detectCircle


def getScreenSize():
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)


# def detectBoard(img, top=0, left=0) -> tuple[(int, int), (int, int)]:
#     scr = img
#     # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#     _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
#     img = cv2.bitwise_not(thresh)

#     lines = cv2.HoughLinesP(img, 1, np.pi / 180, 10, None, 300, 5)
#     a, _, b = lines.shape
#     lines = lines.reshape((a * 2, b // 2))
#     x1, y1 = lines.min(0)
#     x2, y2 = lines.max(0)
#     cv2.rectangle(scr, (x1, y1), (x2, y2), (0, 0, 255), 2)
#     cv2.imshow('img', scr)
#     return x1 + left, y1 + top, x2 + left, y2 + top


def contourDistance(contour1, contour2):
    x1, y1, w1, h1 = cv2.boundingRect(contour1)
    x2, y2, w2, h2 = cv2.boundingRect(contour2)

    center1 = np.array([x1 + w1 / 2, y1 + h1 / 2])
    center2 = np.array([x2 + w2 / 2, y2 + h2 / 2])

    centerDistance = np.linalg.norm(center1 - center2)

    overlapX = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
    overlapY = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))

    if overlapX > 0 and overlapY > 0: 
        return 0  
    else:
        return centerDistance


def groupOverlappingContours(contours, distanceThreshold=10, areaSize=300):
    groupedContours = []
    remainingContours = contours[:] 

    while remainingContours:
        currentContour = remainingContours.pop(0)

        if cv2.contourArea(currentContour) < areaSize:
            continue

        group = [currentContour]
        indicesToRemove = []  

        for i, contour in enumerate(remainingContours):
            if cv2.contourArea(contour) < areaSize:
                continue
            if contourDistance(contour, currentContour) <= distanceThreshold:
                group.append(contour)
                indicesToRemove.append(i) 

        for index in sorted(indicesToRemove, reverse=True):
            del remainingContours[index]

        groupedContour = np.concatenate(group) 
        groupedContours.append(groupedContour)

    return groupedContours


def isInside(coord, rect):
    x1, y1, x2, y2 = rect
    return (x1 <= coord[0] <= x2) and (y1 <= coord[1] <= y2)


def darkImage(img, alpha=1):
    kernel = np.array([[0,   0,   0],
                       [0, alpha, 0],
                       [0,   0,   0]])
    img = cv2.filter2D(img, -1, kernel)
    return img


def valid(move, sizeX=15, sizeY=15):
    if len(move) < 2:
        return False    
    x, y = convertMove(move, sizeY)
    return 0 <= x < (sizeX) and 0 <= y < (sizeY)


def convertMove(move, sizeY=15):
    return [ord(move[0]) - 97, sizeY - int(move[1:])]


def get(string, sizeX=15, sizeY=15):
    if string and string[0]:
        cur = string[0]
        string = string[1:]
        while string:
            if string[0].isnumeric():
                cur += string[0]
                string = string[1:]
            else:
                break
        cur = cur if valid(cur, sizeX, sizeY) else ''
        if cur:
            return [convertMove(cur, sizeY)] + get(string, sizeX, sizeY)
        else:
            return get(string, sizeX, sizeY)
    else:
        return []


def imgCrop(x1, y1, h, w):
    sct = mss.mss()
    img = cv2.cvtColor(np.array(sct.grab(sct.monitors[0])), cv2.COLOR_BGR2RGB)
    img = img[y1:y1+h, x1:x1+w]
    return img


class Listener:
    def __init__(self):
        self.__listKey = []
        self.__hotkey = {}
        self.__validKey = {}

        self.__thread = Thread(target=self.start)
        self.__thread.daemon = True
        self.__thread.start()

    def __getKeySCNCode(self, key):
        return min(keyboard.key_to_scan_codes(key))
    
    def __hashHotkey(self, listKey):
        out = 0
        for key in listKey:
            out |= 1 << self.__validKey[key]
        return hex(out)

    def start(self):
        while True:
            key = keyboard.read_event()
            keyName = self.__getKeySCNCode(key.name.lower())
            if keyName in self.__validKey and key.event_type == 'down':
                if keyName not in self.__listKey:
                    self.__listKey.append(keyName)
                    _hashHK = self.__hashHotkey(self.__listKey)
                    if _hashHK in self.__hotkey:
                        self.__hotkey[_hashHK]()
            else:
                self.__listKey.clear()
                continue

    def addHotKey(self, hotkey: str, func):                
        for _hotkey in hotkey.split('+'):
            key = self.__getKeySCNCode(_hotkey.lower())
            if key not in self.__validKey:
                self.__validKey[key] = max(self.__validKey.values()) + 1 if self.__validKey.values() else 0
        hotkey = self.__hashHotkey([self.__getKeySCNCode(value) for value in hotkey.split('+')])
        self.__hotkey[hotkey] = func


class ScreenCapture(tk.Toplevel):
    SCT = mss.mss()
    def __init__(self, master):
        super().__init__(master)
        self.__w, self.__h = getScreenSize()
        self.attributes('-topmost', True)
        self.geometry(f'{self.__w}x{self.__h}')
        self.overrideredirect(True)

        self.canvasFrame = tk.Canvas(self, bg='white', highlightthickness=0)
        self.canvasFrame.pack(fill=tk.BOTH, expand=True)

        self.__img    = cv2.cvtColor(np.array(self.SCT.grab(self.SCT.monitors[0])), cv2.COLOR_BGR2RGB)
        self.__imgTk  = Image.fromarray(darkImage(self.__img, 0.6))
        self.__imgTk  = ImageTk.PhotoImage(self.__imgTk)
        self.canvasFrame.create_image(0, 0, image=self.__imgTk, anchor='nw')

        self.__startX = None
        self.__startY = None
        self.__rect   = None        

        self.canvasFrame.bind('<ButtonPress-1>', self.onMousePress)
        self.canvasFrame.bind('<B1-Motion>', self.onMouseHold)
        self.canvasFrame.bind('<ButtonRelease-1>', self.onMouseRelease)        

    def onMousePress(self, event):
        self.__startX = event.x
        self.__startY = event.y

    def onMouseHold(self, event):
        if self.__startX is not None and self.__startY is not None:
            if self.__rect:
                self.canvasFrame.delete(self.__rect)
            self.__rect = self.canvasFrame.create_rectangle(
                self.__startX, self.__startY, event.x, event.y, outline='#ffffff', width=3)
            
    def onMouseRelease(self, event):
        x1 = min(self.__startX, event.x)
        y1 = min(self.__startY, event.y)
        x2 = max(self.__startX, event.x)
        y2 = max(self.__startY, event.y)   

        self.__startX = x1
        self.__startY = y1

        self.canvasFrame.delete("all")
        self.after(100, self.__screenshot, x1, y1, x2, y2)

    def __screenshot(self, x1, y1, x2, y2):        
        self.__img = self.__img[y1:y2, x1:x2]
        cv2.imwrite('img.png', self.__img)
        self.destroy()

    def get(self):
        self.wait_window()
        return self.__img, self.__startX, self.__startY


class Board:
    def __init__(self, point1, size, sizeX, sizeY):
        self.__x1, self.__y1 = point1        
        self.__w, self.__h = size
        self.__disX = self.__w / (sizeX - 1)
        self.__disY = self.__h / (sizeY - 1)
        self.__sizeX, self.__sizeY = sizeX, sizeY

    def click(self, x, y):
        win32api.SetCursorPos((round(x), round(y)))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

        time.sleep(0.05)
        # win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        # win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

    def __move2Coord(self, x, y):
        return self.__x1 + round(x * self.__disX), (self.__y1 + round(y * self.__disY))

    def setPos(self, pos):
        posString = get(pos, self.__sizeX, self.__sizeY)
        for move in posString:
            self.click(*self.__move2Coord(*move))


class CustomArr:
    def __init__(self):
        self.__data = []

    def __setitem__(self, index, value):
        if index >= len(self.__data):
            self.__data.extend([None] * (index - len(self.__data) + 1))
        self.__data[index] = value

    def __getitem__(self, index):
        return self.__data[index]
    
    def __iter__(self):
        return iter(self.__data)
    
    def __repr__(self):
        return repr(self.__data)
    

class ArrangedArr:
    def __init__(self):
        self.__data: CustomArr = CustomArr()
        self.__bIndex = 0
        self.__wIndex = 1

    def add(self, move, label):
        if label.lower() == 'b':
            self.__data[self.__bIndex] = move
            self.__bIndex += 2
        elif label.lower() == 'w':
            self.__data[self.__wIndex] = move
            self.__wIndex += 2

    def get(self):
        return self.__data
