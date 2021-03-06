import numpy as np
import cv2 as cv
import sys

from my_module import extract_color as exc
from my_module import product as pd

class Grabcut:
    BLUE = [255,0,0]        # rectangle color
    RED = [0,0,255]         # PR BG
    GREEN = [0,255,0]       # PR FG
    BLACK = [0,0,0]         # sure BG
    WHITE = [255,255,255]   # sure FG

    DRAW_BG = {'color' : BLACK, 'val' : 0}
    DRAW_FG = {'color' : WHITE, 'val' : 1}
    DRAW_PR_FG = {'color' : GREEN, 'val' : 3}
    DRAW_PR_BG = {'color' : RED, 'val' : 2}

    # setting up flags
    rect = (0,0,1,1)
    drawing = False         # flag for drawing curves
    rectangle = False       # flag for drawing rect
    rect_over = False       # flag to check if rect drawn
    rect_or_mask = 100      # flag for selecting rect or mask mode
    value = DRAW_FG         # drawing initialized to FG
    thickness = 3           # brush thickness

    def __init__(self, filename, product_id, color_id) :
        self.filename = filename
        self.product_id = product_id
        self.color_id = color_id
   
    def onmouse(self, event, x, y, flags, param):
        # Draw Rectangle
        if event == cv.EVENT_RBUTTONDOWN:
            self.rectangle = True
            self.ix, self.iy = x,y

        elif event == cv.EVENT_MOUSEMOVE:
            if self.rectangle == True:
                self.img = self.img2.copy()
                cv.rectangle(self.img, (self.ix, self.iy), (x, y), self.BLUE, 2)
                self.rect = (min(self.ix, x), min(self.iy, y), abs(self.ix - x), abs(self.iy - y))
                self.rect_or_mask = 0

        elif event == cv.EVENT_RBUTTONUP:
            self.rectangle = False
            self.rect_over = True 
            cv.rectangle(self.img, (self.ix, self.iy), (x, y), self.BLUE, 2)
            self.rect = (min(self.ix, x), min(self.iy, y), abs(self.ix - x), abs(self.iy - y))
            self.rect_or_mask = 0
            print(" Now press the key 'n' a few times until no further change \n")

        # draw touchup curves

        if event == cv.EVENT_LBUTTONDOWN:
            if self.rect_over == False:
                print("first draw rectangle \n")
            else:
                self.drawing = True
                cv.circle(self.img, (x,y), self.thickness, self.value['color'], -1)
                cv.circle(self.mask, (x,y), self.thickness, self.value['val'], -1)

        elif event == cv.EVENT_MOUSEMOVE:
            if self.drawing == True:
                cv.circle(self.img, (x, y), self.thickness, self.value['color'], -1)
                cv.circle(self.mask, (x, y), self.thickness, self.value['val'], -1)

        elif event == cv.EVENT_LBUTTONUP:
            if self.drawing == True:
                self.drawing = False
                cv.circle(self.img, (x, y), self.thickness, self.value['color'], -1)
                cv.circle(self.mask, (x, y), self.thickness, self.value['val'], -1)

    def grabcut_image(self):
        # Loading images
        if len(sys.argv) == 2:
            filename = sys.argv[1] # for drawing purposes
        else:
            print("No input image given, so loading default image, lena.jpg \n")
            print("Correct Usage: python grabcut.py <filename> \n")
            filename = self.filename

        self.img = cv.imread(cv.samples.findFile(filename))
        self.img2 = self.img.copy()                                # 원본 이미지 copy 
        self.mask = np.zeros(self.img.shape[:2], dtype = np.uint8) # mask 초기화
        self.output = np.zeros(self.img.shape, np.uint8)           # output 이미지 초기화

        # input and output windows
        cv.namedWindow('output')
        cv.namedWindow('input')
        cv.setMouseCallback('input', self.onmouse)
        cv.moveWindow('input', self.img.shape[1]+10,90)

        print(" Instructions: \n")
        print(" Draw a rectangle around the object using right mouse button \n")

        while(1):

            cv.imshow('output', self.output)
            cv.imshow('input', self.img)
            k = cv.waitKey(1)

            # key bindings
            if k == 27:         # esc to exit
                break
            elif k == ord('1'): # BG drawing
                print(" mark background regions with right mouse button \n")
                self.value = self.DRAW_BG
            elif k == ord('2'): # FG drawing
                print(" mark foreground regions with left mouse button \n")
                self.value = self.DRAW_FG
            elif k == ord('3'): # PR_BG drawing
                self.value = self.DRAW_PR_BG
            elif k == ord('4'): # PR_FG drawing
                self.value == self.DRAW_PR_FG
            elif k == ord('c'): # copy input image to output
                print("copy image")
                self.mask = np.ones(self.img.shape[:2], dtype = np.uint8)
            elif k == ord('s'): # save image
                bar = np.zeros((self.img.shape[0], 5, 3), np.uint8)
                res = np.hstack((bar, self.output))
                resultfile = 'extract_image/'+self.product_id+"/"+self.color_id+'.png' # 해당 디렉토리에 추출된 이미지 저장
                cv.imwrite(resultfile, res)
                color_data = exc.extract_color(resultfile)                             # 저장된 이미지에서 색 추출
                print(color_data)
                pd.add_prodcut_color_to_file(self.product_id,self.color_id,color_data) # 추출할 색 이미지 데이터 파일에 저장
                print(" Result saved as image \n")
            elif k == ord('r'): # reset everything
                print("resetting \n")
                self.rect = (0,0,1,1)
                self.drawing = False
                self.rectangle = False
                self.rect_or_mask = 100
                self.rect_over = False
                self.value = self.DRAW_FG
                self.img = self.img2.copy()
                self.mask = np.zeros(self.img.shape[:2], dtype = np.uint8) # mask 초기화
                self.output = np.zeros(self.img.shape, np.uint8)           # output 이미지 초기화
            elif k == ord('n'): # input에서 전경(FG)으로 마스킹한 부분을 output에 표시
                print(""" For finer touchups, mark foreground and background after pressing keys 0-3
                and again press 'n' \n""")
                try :
                    if (self.rect_or_mask == 0):         # grabcut with rect
                        bgdmodel = np.zeros((1, 65), np.float64)
                        fgdmodel = np.zeros((1, 65), np.float64)
                        cv.grabCut(self.img2, self.mask, self.rect, bgdmodel, fgdmodel, 1, cv.GC_INIT_WITH_RECT)
                        self.rect_or_mask = 1
                    elif self.rect_or_mask == 1:         # grabcut with mask
                        bgdmodel = np.zeros((1, 65), np.float64)
                        fgdmodel = np.zeros((1, 65), np.float64)
                        cv.grabCut(self.img2, self.mask, self.rect, bgdmodel, fgdmodel, 1, cv.GC_INIT_WITH_MASK)
                except :
                    import traceback
                    traceback.print_exc()
            
            mask2 = np.where((self.mask==1) + (self.mask==3), 255, 0).astype('uint8')
            self.output = cv.bitwise_and(self.img2, self.img2, mask=mask2)

        cv.destroyAllWindows()

if __name__ == '__main__':
    print(__doc__)
    image = Grabcut("test","test","model.jpg")
    image.grabcut_image()
    
# https://github.com/opencv/opencv/blob/master/samples/python/grabcut.py