import ctypes
import random
import sys
import time
import keyboard
import pyautogui
import threading
import pywinctl as pwc
from PIL import Image
import cv2
import os.path
import PySimpleGUI as sg
import numpy as np

# stuff I got online

PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]
class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]
class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]
class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]
class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]
class MouseKey:
    def __init__(self, char, press_virtual_code, release_virtual_code, press_dd_code, release_dd_code, press_logi_code,
                 release_logi_code):
        self.char = char
        self.press_virtual_code = press_virtual_code
        self.release_virtual_code = release_virtual_code
        self.press_dd_code = press_dd_code
        self.release_dd_code = release_dd_code
        self.press_logi_code = press_logi_code
        self.release_logi_code = release_logi_code
    def __repr__(self):
        return f"MouseKey(name='{self.char}', press_virtual_code={self.press_virtual_code}, " \
               f"release_virtual_code={self.release_virtual_code},press_dd_code={self.press_dd_code}," \
               f"release_dd_code={self.release_dd_code})"
class Mouse:
    MOUSE_LEFT = MouseKey('Mouse Left', 0x0002, 0x0004, 1, 2, 1, 1)
    MOUSE_RIGHT = MouseKey('Mouse Right', 0x0008, 0x0010, 4, 8, 2, 2)
    MOUSE_MIDDLE = MouseKey('Mouse Middle', 0x0020, 0x0040, 16, 32, 3, 3)
    MOUSE_X = MouseKey('Mouse X', 0x0080, 0x0100, 64, 128, 4, 4)
    MOUSE_WHEEL = MouseKey('Mouse Wheel', 0x0800, 0x0000, 0, 0, 0, 0)
    MOUSE_MOVE = MouseKey('Mouse Move', 0x0001, 0x0000, 0, 0, 0, 0)
screenwidth, screenheight = ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)
# end

PATH = "./pic/screenshot.png"
f = open('./battlelog/log.txt', 'a+')
menu = "战争雷霆蓝莓派助手简约（无高级功能）版：\n" \
       "▶图像设定：\n分辨率：1270x720  显示模式：窗口模式\nUI大小：100%\n" \
       "W仰，S俯，\nshift切换视角，b打开弹仓\n" \
       "不一定炸得到战区就是了\n"

sg.theme('DarkBlue2')

updateLog = [
    [sg.Text("免责申明：\n本软件是大学暑期图像识别基础课\n课上实践作业，\n没有用到高深技术，\n现结课后根据规定免费公开，\n请勿在技术学习范畴之外使用\n或售卖本软件，违者后果自负", key="-log-")]]

layout = [[sg.Text(menu)],
          [sg.Button("轰炸机"),sg.VSeperator(), sg.Button("攻击机"), sg.VSeperator(), sg.Button("停止并退出")],
          [sg.Button("送死模式")],
          [sg.Column(layout=updateLog, size=(270, 150))]]

turntime = 0
gotime = 0
planeType = -1
goDie = False
windowIsAnchored = True
redMask = (np.array([0,150,150]),np.array([20,255,255]),np.array([160,150,150]),np.array([180,255,255]))

def click(location):
    # click a certain location on the screen
    pyautogui.moveTo(location[0], location[1])
    time.sleep(0.2)
    pyautogui.mouseDown(button='left')
    time.sleep(0.2)
    pyautogui.mouseUp(button='left')

def spamESC(times):
    for i in range(times):
        pressWithDelay('esc', 0.1, 0.5)


def log(message):
    # put the log in the GUI and the text log
    print(message)
    text = window["-log-"]
    text.update(message)
    curr_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    try:
        f.write("[" + curr_time + "] " + message + "\n")
    except:
        print("出现了日志写入错误，可能是计算机之间不同编码的问题吧？")


def hasImage(name, threshold, message):
    # returns true if the current screenshot has the desired image
    wholeWindow = cv2.imread(PATH)
    targetImg = cv2.imread("./model/" + name + ".png")
    "start matching"
    result = cv2.matchTemplate(wholeWindow, targetImg, cv2.TM_CCORR_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    print(name + "\t" + str(max_val))
    if max_val > threshold:
        return True
    else:
        if message is not None:
            log(message)
        return False

def getBase(name, threshold, image, baseFound):
    # returns true if the current screenshot has the desired image
    targetImg = cv2.imread("./model/" + name + ".png")
    height, width, channel = targetImg.shape
    "start matching"
    result = cv2.matchTemplate(image, targetImg, cv2.TM_CCORR_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # print(name + "\t" + max_loc + "\t" + str(max_val) + pyautogui.position())
    ul = cv2.minMaxLoc(result)[3]
    lr = (ul[0] + width, ul[1] + height)
    center = (int((ul[0] + lr[0]) / 2), int((ul[1] + lr[1]) / 2))
    deviation = center[0] - pyautogui.position().x
    if baseFound:
        if abs(deviation) > 125:
            deviation = -1
    if max_val > threshold:
        moveMouse(deviation + 1, 0)
        if deviation < 100:
            return True
    return False



def moveMouse(x, y):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(x, y, 0, Mouse.MOUSE_MOVE.press_virtual_code, 0, ctypes.pointer(extra))
    rx = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(rx), ctypes.sizeof(rx))

def getButtonLocation(name):
    # get the button's location
    wholeWindow = cv2.imread(PATH)
    targetImg = cv2.imread("./model/" + name + ".png")
    "start matching"
    height, width, channel = targetImg.shape
    result = cv2.matchTemplate(wholeWindow, targetImg, cv2.TM_SQDIFF_NORMED)
    ul = cv2.minMaxLoc(result)[2]
    lr = (ul[0] + width, ul[1] + height)
    center = (int((ul[0] + lr[0]) / 2), int((ul[1] + lr[1]) / 2))
    return center


def escapeBuying(window):
    # if a ship is researched, escape buying via the item shop
    screenshot(window)
    click(getButtonLocation("researchdone"))
    time.sleep(3)
    getScreen(window, PATH)
    if hasImage("newshipresearched", 0.91, None) and not hasImage("partsdone", 0.91, None):
        screenshot(window)
        click(getButtonLocation("shop"))
        screenshot(window)
        click(getButtonLocation("itemshop"))
        screenshot(window)
        spamESC(3)
    partsDone(window)


def partsDone(window):
    time.sleep(1)
    screenshot(window)
    if hasImage("autoresearch", 0.92, None):
        click(getButtonLocation("autoresearch"))
        time.sleep(10)
        spamESC(15)


def getScreen(window, location):
    # screenshot the current screen
    left, top = window.topleft
    right, bottom = window.bottomright
    pyautogui.screenshot(location)
    global windowIsAnchored
    if windowIsAnchored:
        img = Image.open(location)
        img = img.crop((left, top, right, bottom))
        img.save(location)

def screenshot(window):
    time.sleep(0.1)
    getScreen(window, PATH)
    time.sleep(0.2)


def pressWithDelay(c, d, t):
    # press the button c, for d seconds, and wait t seconds
    keyboard.press(c)
    time.sleep(d)
    keyboard.release(c)
    time.sleep(t)


def maneuverPattern(window, baseFound, name):
    img = cv2.imread(PATH)

    # img = img[int(img.width/4):int(3*img.width/4),:]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    global redMask
    mask1 = cv2.inRange(hsv, redMask[0], redMask[1])
    mask2 = cv2.inRange(hsv, redMask[2], redMask[3])
    mask = mask1 + mask2
    maskedImg = cv2.bitwise_and(img, img, mask=mask)
    baseFound = getBase(name, 0.65, maskedImg, baseFound)
    return baseFound



def attackPattern():
    img = cv2.imread(PATH)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    global redMask
    mask1 = cv2.inRange(hsv, redMask[0], redMask[1])
    mask2 = cv2.inRange(hsv, redMask[2], redMask[3])
    mask = mask1 + mask2
    maskedImg = cv2.bitwise_and(img, img, mask=mask)
    targetImg = cv2.imread("./model/basebombing.png")
    height, width, channel = targetImg.shape
    "start matching"
    result = cv2.matchTemplate(maskedImg, targetImg, cv2.TM_CCORR_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    print("bombing run\t" + str(max_loc) + "\t" + str(max_val))
    if max_val > 0.42:
        print("base in sight")
        ul = cv2.minMaxLoc(result)[3]
        lr = (ul[0] + width, ul[1] + height)
        center = (int((ul[0] + lr[0]) / 2), int((ul[1] + lr[1]) / 2))
        deviation = center[0] - pyautogui.position().x
        moveMouse(int(deviation/2), 0)
        if center[1] > 330 and center[1] < 380:
            for i in range(20):
                pressWithDelay('space', 0.03, 0.03)


def saveResults(window, times):
    # Save the results after a battle is done
    log("保存收益截图，最多保存" + str(times) + "张，请按需清理")
    i = 0
    while i < times:
        temppath = './battlelog/result' + str(i) + '.png'
        if not os.path.isfile(temppath):
            getScreen(window, temppath)
            break
        else:
            i = i + 1
    time.sleep(0.5)


def timeoutEscape():
    # a dumb way to escape timeouts: spam esc many times.
    spamESC(10)


def WTScript(window):
    getScreen(window, PATH)
    windowName = window.title
    global planeType
    global goDie
    # print(windowName)
    if not (windowName.__contains__("试") or windowName.__contains__("战") or windowName.__contains__("载")):
        # We are at the hanger. Have to enter a game first
        if hasImage("air", 0.91, "未检测到空战！可能被阻挡或未调成海战"):
            if hasImage("enterbattle", 0.95, "未检测到加入游戏！"):
                click(getButtonLocation("enterbattle"))
                screenshot(window)
                time.sleep(3)
                if hasImage("downloadprompt", 0.98, None):
                    # If the texture download happens to be there, close it
                    click(getButtonLocation("downloadprompt"))
                    screenshot(window)
                    if hasImage("exitout", 0.92, None):
                        click(getButtonLocation(("exitout")))
                        screenshot(window)
                    time.sleep(3)
                while window.title.__contains__("等"):
                    time.sleep(5)
                log("已进入战斗！")
        elif hasImage("newshipresearched", 0.97, None):
            escapeBuying(window)
        elif hasImage("researchdone", 0.97, None):
            timeoutEscape()
        elif hasImage("autoresearch", 0.95, None):
            partsDone(window)
        elif hasImage("cancelsmall", 0.98, None):
            click(getButtonLocation("cancelsmall"))
        elif hasImage("exitout", 0.92, None):
            click(getButtonLocation("exitout"))
        else:
            timeoutEscape()
    elif windowName.__contains__("试"):
        # We are in testing mode. Under this mode it only fires to check if the attack pattern works
        attackPattern()
    elif windowName.__contains__("载"):
        # We are loading into one game
        time.sleep(4)
    elif windowName.__contains__("战"):
        # We are currently in a game
        # Then, let it auto spawn to avoid being locked on
        i = 0
        while not hasImage("enterspec", 0.97, None):
            i = i + 1
            screenshot(window)
            if i > 900:
                break
        time.sleep(1)
        pressWithDelay('enter', 0.2, 0.1)
        log("加入战斗")
        time.sleep(16)
        i = 0
        foundBase = False
        # Lock on to the enemy and open fire
        while windowName.__contains__("战"):
            i = i + 1
            windowName = window.title
            screenshot(window)
            if hasImage("pressJ", 0.96, None):
                pressWithDelay("j", 5, 5)
            if i == 4:
                if planeType == 0:
                    moveMouse(0, 60)
                elif planeType == 1:
                    moveMouse(0, -60)
                time.sleep(0.1)
                moveMouse(10, 0)
                time.sleep(0.1)
                moveMouse(-10, 0)
            if not goDie:
                if i > 8 and i < 40:
                    foundBase = maneuverPattern(window, foundBase, "basethirdRED")
                elif i == 60:
                    if planeType == 0:
                        pressWithDelay("shift", 0.3, 0.2)
                        pressWithDelay("shift", 0.3, 0.2)
                        pressWithDelay("b", 0.3, 0.3)
                elif i > 60 and i < 200:
                    attackPattern()
            if i == 200:
                if planeType == 0:
                    moveMouse(0, -60)
                elif planeType == 1:
                    moveMouse(0, 60)
            if i > 500:
                pressWithDelay("j", 5, 5)
                i = -100
            elif i > 700:
                # Game is stuck, try to escape
                log("检测到卡死")
                timeoutEscape()
                getScreen(window, PATH)
                time.sleep(360)
            if hasImage("youdied", 0.95, None):
                # died before the game ended
                log("已死亡，返回主界面中，\n为防止网络情况卡死，等待10秒")
                getScreen(window, PATH)
                time.sleep(1)
                while hasImage("youdied", 0.94, None):
                    click(getButtonLocation("youdied"))
                    getScreen(window, PATH)
                    time.sleep(1)
                time.sleep(12)
                break
        # game is over
        log("结束战斗，等待结算")
        # wait for the points
        time.sleep(6)
        screenshot(window)
        researchDone = False
        i = 0
        while not hasImage("gotobase", 0.97, None):
            i = i + 1
            if i > 30:
                log("检测到卡死")
                timeoutEscape()
                break
            time.sleep(0.5)
            getScreen(window, PATH)
            time.sleep(0.5)
            if hasImage("crates", 0.95, None):
                # unlocked crates
                log("===出了个箱子，记得查看背包===")
                getScreen(window, PATH)
                time.sleep(15)
                pressWithDelay('esc', 0.1, 0.5)
            if hasImage("researchdone", 0.98, None):
                # new ship got researched. To avoid spending all SL, we glitch the research out
                researchDone = True
                log("===解锁了配件或新船===")
                time.sleep(5)
                saveResults(window, 1000)
                escapeBuying(window)
                break
            if hasImage("exitout", 0.91, None):
                click(getButtonLocation("exitout"))
        if not researchDone:
            saveResults(window, 1000)
            getScreen(window, PATH)
            time.sleep(0.5)
            log("结算完成，返回主界面")
            click(getButtonLocation("gotobase"))
            getScreen(window, PATH)
            time.sleep(0.5)
            if hasImage("newshipresearched", 0.97, None) or hasImage("autoresearch", 0.97, None):
                # new ship got researched. To avoid spending all SL, we glitch the research out
                log("===解锁了配件或新船===")
                escapeBuying(window)
        time.sleep(1)
        getScreen(window, PATH)


def anchorWindow(window):
    # move war thunder to the top left of the screen
    global windowIsAnchored
    if windowIsAnchored:
        try:
            window.moveTo(0, 0)
            time.sleep(0.5)
        except:
            windowIsAnchored = False


def detectWindow():
    # detect if the current window is war thunder. If not, don't input anything to avoid accidents
    while True:
        try:
            window = pwc.getActiveWindow()
            if window is None:
                continue
            windowName = window.title
            if windowName.__contains__("War Thunder"):
                "Currently in War Thunder"
                anchorWindow(window)
                WTScript(window)
                time.sleep(0.5)
            else:
                "Currently not in War Thunder"
                print("未检测到战争雷霆！")
                time.sleep(3)

        except KeyboardInterrupt:
            break


def startScript():
    # start the whole script
    detectWindow()


if __name__ == '__main__':
    isRunning = False
    window = sg.Window(title="蓝莓派空战助手", layout=layout)
    app = threading.Thread(target=startScript, daemon=True)
    while True:
        event, values = window.read()
        # End program if user closes window or
        # presses the OK button
        if event == "停止并退出" or event == sg.WIN_CLOSED:
            f.close()
            sys.exit()
        if event == "攻击机" and not isRunning:
            planeType = 1
            isRunning = True
            log("开始运行")
            app.start()
        if event == "轰炸机" and not isRunning:
            planeType = 0
            isRunning = True
            log("开始运行")
            app.start()
        if event == "送死模式" and not goDie:
            goDie = True
            log("已开启送死模式！")
            bt = window["送死模式"]
            bt.update("关闭送死模式")
        elif event == "送死模式" and goDie:
            goDie = False
            log("已开启炸战区模式！\n请注意，可能因为炸战区而无法死亡！")
            bt = window["送死模式"]
            bt.update("开启送死模式")

