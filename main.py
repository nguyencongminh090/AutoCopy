import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.tooltip import ToolTip
from ttkbootstrap.toast import ToastNotification

from utils import *



class Main(ttk.Window):
    def __init__(self):
        super().__init__()
        self.title('AutoCopy v1.0')
        self.geometry()
        self.resizable(0, 0)
        
        # Label
        self.__label = ttk.Label(self, text='x')
        self.__label.grid(column=6, row=0, padx=5, pady=5, sticky='news')

        # TextBox
        self.__posTextBox = ttk.Entry(self, width=50)
        self.__sizeXTextBox = ttk.Entry(self, text=15, width=5, justify='center')
        self.__sizeYTextBox = ttk.Entry(self, width=5, justify='center')

        self.__sizeXTextBox.insert('0', '15')
        self.__sizeYTextBox.insert('0', '15')

        self.__toolTipPos = ToolTip(self.__posTextBox, text='Paste your position here')
        self.__toolTipPos = ToolTip(self.__sizeXTextBox, text='X')
        self.__toolTipPos = ToolTip(self.__sizeYTextBox, text='Y')

        self.__posTextBox.grid(column=0, row=0, padx=5, pady=5, sticky='news')
        self.__sizeXTextBox.grid(column=5, row=0, padx=5, pady=5, sticky='news')
        self.__sizeYTextBox.grid(column=7, row=0, padx=5, pady=5, sticky='news')

        # Button
        self.__buttonSelectBoard = ttk.Button(self, text='Select Board')
        self.__buttonStart = ttk.Button(self, text='Start')
        self.__buttonGetPos = ttk.Button(self, text='Get')
        self.__buttonReCapture = ttk.Button(self, text='ReCapture')

        self.__buttonSelectBoard.grid(column=1, row=0, padx=5, pady=5, sticky='we')
        self.__buttonStart.grid(column=2, row=0, padx=5, pady=5, sticky='we')
        self.__buttonGetPos.grid(column=3, row=0, padx=5, pady=5, sticky='we')
        self.__buttonReCapture.grid(column=4, row=0, padx=5, pady=5, sticky='we')

        self.__buttonSelectBoard.configure(command=self.screenCapture)
        self.__buttonStart.configure(command=self.start)
        self.__buttonGetPos.configure(command=self.get)       
        self.__buttonReCapture.configure(command=self.updateImg)
        

        # Toast Notification
        self.__toast = ToastNotification(
                                        title="Autocopy: Error",
                                        message="No Board Found",
                                        duration=10000,
                                        )

        # Backend
        self.__x1, self.__y1, self.__w, self.__h = None, None, None, None
        self.__img, self.__left, self.__top = None, None, None
        self.__boardState = None

    def screenCapture(self):
        self.__img, self.__left, self.__top = ScreenCapture(self).get()
        try:
            self.__x1, self.__y1, self.__w, self.__h = detectBoard(self.__img, self.__top, self.__left)        
            self.__boardState = True
        except:
            self.__toast.show_toast()

    def start(self):
        if self.__boardState:
            board = Board((self.__x1, self.__y1), (self.__w, self.__h),\
                        int(self.__sizeXTextBox.get()), int(self.__sizeYTextBox.get()))
            board.setPos(self.__posTextBox.get())
        else:
            self.__toast.show_toast()

    def get(self):
        moves = detectCircle(self.__img, (self.__x1 - self.__left, 
                                          self.__y1 - self.__top,
                                          self.__w, self.__h),
                                          int(self.__sizeXTextBox.get()), int(self.__sizeYTextBox.get()))
        self.__posTextBox.delete('0', 'end')
        self.__posTextBox.insert('0', ''.join(moves))


    def updateImg(self):
        self.__img = imgCrop(self.__left, 
                             self.__top, 
                             *self.__img.shape[:2])
        cv2.imshow('Test', self.__img)

            
def main():
    window = Main()
    window.mainloop()


if __name__ == '__main__':
    main()