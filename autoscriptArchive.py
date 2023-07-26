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

PATH = "./pic/screenshot.png"
MAP = "./pic/map.png"
MAPBIG = "./pic/mapbig.png"
f = open('./battlelog/log.txt', 'a+')
menu = "战争雷霆蓝莓派助手简约版：\n" \
       "▶图像设定：\n分辨率：1920x1080  显示模式：全屏窗口\nUI大小：100%\n" \
       "▶主选项->陆战设置：\n战术地图比例：最大（133%）\n" \
       "▶按键设置->陆战：\n短停：`" \
       "除了用来挂的车，不要带任何其他载具。\n" \
       "请使用速度快的高级载具，维修费最好不超过五千。\n" \
       "点击开始后，请把战争雷霆放在前台。\n" \
       "本脚本非注入式，是图像识别，所以不能后台运行"


captureMode = False

sg.theme('DarkBlue2')

test_cord = Image.open("./model/route/route/route1.png")
progress = 0


updateLog = [
    [sg.Text("免责申明：\n本软件是大学暑期图像识别基础课\n课上实践作业，\n没有用到高深技术，\n现结课后根据规定免费公开，\n请勿在技术学习范畴之外使用\n或售卖本软件，违者后果自负", key="-log-")]]

layout = [[sg.Text(menu)],
          [sg.Button("开始"), sg.VSeperator(),sg.Button("截图"), sg.VSeperator(), sg.Button("停止并退出")],
          [sg.Column(layout=updateLog, size=(310, 150))]]

arrow = cv2.imread("./model/arrow1.png")

pointAloc = 0
pointBloc = 0
pointCloc = 0
myloc = 0

def click(location):
    # click a certain location on the screen
    pyautogui.moveTo(location[0], location[1])
    time.sleep(0.05)
    pyautogui.mouseDown(button='left')
    time.sleep(0.2)
    pyautogui.mouseUp(button='left')
    time.sleep(0.01)
    pyautogui.moveTo(90, 90)
    time.sleep(0.01)

def pressWithDelay(c, d, t):
    # press the button c, for d seconds, and wait t seconds
    keyboard.press(c)
    time.sleep(d)
    keyboard.release(c)
    time.sleep(t)

def spamESC(times):
    for i in range(times):
        pressWithDelay('esc', 0.1, 0.5)

def timeoutEscape():
    # a dumb way to escape timeouts: spam esc many times.
    spamESC(10)

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

def screenshot():
    time.sleep(0.5)
    getScreen(PATH)
    time.sleep(0.5)

def getScreen(location):
    # screenshot the current screen
    pyautogui.screenshot(location)

def saveResults(window, times):
    # Save the results after a battle is done
    log("保存收益截图，最多保存" + str(times) + "张，请按需清理")
    i = 0
    while i < times:
        temppath = './battlelog/result' + str(i) + '.png'
        if not os.path.isfile(temppath):
            getScreen(temppath)
            break
        else:
            i = i + 1
    time.sleep(0.5)

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
                WTScript(window)
            else:
                "Currently not in War Thunder"
                print("未检测到战争雷霆！")
                time.sleep(3)

        except KeyboardInterrupt:
            break

def getdistance(a, b):
    return sum(abs(val1-val2) for val1, val2 in zip(a,b))


def rotate_image(image, angle):
    image_center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, -angle, 1.0)
    result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
    return result

def invariantMatchTemplate(rgbimage, rgbtemplate, method, matched_thresh, rot_range, rot_interval, minmax):
    """
    rgbimage: RGB image where the search is running.
    rgbtemplate: RGB searched template. It must be not greater than the source image and have the same data type.
    method: [String] Parameter specifying the comparison method
    matched_thresh: [Float] Setting threshold of matched results(0~1).
    rgbdiff_thresh: [Float] Setting threshold of average RGB difference between template and source image.
    rot_range: [Integer] Array of range of rotation angle in degrees. Example: [0,360]
    rot_interval: [Integer] Interval of traversing the range of rotation angle in degrees.
    scale_range: [Integer] Array of range of scaling in percentage. Example: [50,200]
    scale_interval: [Integer] Interval of traversing the range of scaling in percentage.
    rm_redundant: [Boolean] Option for removing redundant matched results based on the width and height of the template.
    minmax:[Boolean] Option for finding points with minimum/maximum value.

    Returns: List of satisfied matched points in format [[point.x, point.y], angle, scale].
    """
    image_maxwh = rgbimage.shape
    height, width, numchannel = rgbtemplate.shape
    all_points = []
    if minmax == False:
        for next_angle in range(rot_range[0], rot_range[1], rot_interval):
            if next_angle == 0:
                rotated_template = rgbtemplate
            else:
                rotated_template = rotate_image(rgbtemplate, next_angle)
            if method == "TM_CCOEFF":
                matched_points = cv2.matchTemplate(rgbimage, rotated_template, cv2.TM_CCOEFF)
                satisfied_points = np.where(matched_points >= matched_thresh)
            elif method == "TM_CCOEFF_NORMED":
                matched_points = cv2.matchTemplate(rgbimage, rotated_template, cv2.TM_CCOEFF_NORMED)
                satisfied_points = np.where(matched_points >= matched_thresh)
            elif method == "TM_CCORR":
                matched_points = cv2.matchTemplate(rgbimage, rotated_template, cv2.TM_CCORR)
                satisfied_points = np.where(matched_points >= matched_thresh)
            elif method == "TM_CCORR_NORMED":
                matched_points = cv2.matchTemplate(rgbimage, rotated_template, cv2.TM_CCORR_NORMED)
                satisfied_points = np.where(matched_points >= matched_thresh)
            elif method == "TM_SQDIFF":
                matched_points = cv2.matchTemplate(rgbimage, rotated_template, cv2.TM_SQDIFF)
                satisfied_points = np.where(matched_points <= matched_thresh)
            elif method == "TM_SQDIFF_NORMED":
                matched_points = cv2.matchTemplate(rgbimage, rotated_template, cv2.TM_SQDIFF_NORMED)
                satisfied_points = np.where(matched_points <= matched_thresh)
            else:
                print("the fuck?")
            for pt in zip(*satisfied_points[::-1]):
                all_points.append([pt, next_angle])
    else:
        for next_angle in range(rot_range[0], rot_range[1], rot_interval):
            if next_angle == 0:
                rotated_template = rgbtemplate
            else:
                rotated_template = rotate_image(rgbtemplate, next_angle)
            if method == "TM_CCOEFF":
                matched_points = cv2.matchTemplate(rgbimage, rotated_template, cv2.TM_CCOEFF)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matched_points)
                if max_val >= matched_thresh:
                    all_points.append([max_loc, next_angle, max_val])
            elif method == "TM_CCOEFF_NORMED":
                matched_points = cv2.matchTemplate(rgbimage, rotated_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matched_points)
                if max_val >= matched_thresh:
                    all_points.append([max_loc, next_angle, max_val])
            elif method == "TM_CCORR":
                matched_points = cv2.matchTemplate(rgbimage, rotated_template, cv2.TM_CCORR)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matched_points)
                if max_val >= matched_thresh:
                    all_points.append([max_loc, next_angle, max_val])
            elif method == "TM_CCORR_NORMED":
                matched_points = cv2.matchTemplate(rgbimage, rotated_template, cv2.TM_CCORR_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matched_points)
                if max_val >= matched_thresh:
                    all_points.append([max_loc, next_angle, max_val])
            elif method == "TM_SQDIFF":
                matched_points = cv2.matchTemplate(rgbimage, rotated_template, cv2.TM_SQDIFF)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matched_points)
                if min_val <= matched_thresh:
                    all_points.append([min_loc, next_angle, min_val])
            elif method == "TM_SQDIFF_NORMED":
                matched_points = cv2.matchTemplate(rgbimage, rotated_template, cv2.TM_SQDIFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matched_points)
                if min_val <= matched_thresh:
                    all_points.append([min_loc, next_angle, min_val])
        if method == "TM_CCOEFF":
            all_points = sorted(all_points, key=lambda x: -x[2])
        elif method == "TM_CCOEFF_NORMED":
            all_points = sorted(all_points, key=lambda x: -x[2])
        elif method == "TM_CCORR":
            all_points = sorted(all_points, key=lambda x: -x[2])
        elif method == "TM_CCORR_NORMED":
            all_points = sorted(all_points, key=lambda x: -x[2])
        elif method == "TM_SQDIFF":
            all_points = sorted(all_points, key=lambda x: x[2])
        elif method == "TM_SQDIFF_NORMED":
            all_points = sorted(all_points, key=lambda x: x[2])

    points_list = all_points
    return points_list


def hasImage(name, threshold, message):
    # returns true if the current screenshot has the desired image
    wholeWindow = cv2.imread(PATH)
    targetImg = cv2.imread("./model/" + name + ".png")
    "start matching"
    result = cv2.matchTemplate(wholeWindow, targetImg, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # log(name + "\t" + str(max_val))
    if max_val > threshold:
        return True
    else:
        if message is not None:
            log(message)
        return False

def checkforrepeats(maplib, threshold):
    # returns true if the current screenshot has the desired image
    pastmap = cv2.imread(maplib)
    currentmap = cv2.imread(MAP)
    "start matching"
    result = cv2.matchTemplate(pastmap, currentmap, cv2.TM_CCOEFF_NORMED)
    # err = cv2.norm(pastmap, currentmap, cv2.NORM_L2)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # print(maplib + "\t" + str(max_val))
    if max_val > threshold:
        return True, max_val
    else:
        return False, max_val

def locatePoint(point, threshold, map):
    targetImg = cv2.imread("./model/Point" + point + ".png")
    "start matching"
    result = cv2.matchTemplate(map, targetImg, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    loc = np.where(result > threshold)
    print("Point" + point + "\t" + str(max_val))
    x, y = 0, 0
    for pt in zip(*loc[::-1]):
        img = Image.open(MAP)
        img = img.crop((pt[0], pt[1], pt[0]+20, pt[1]+20))
        img.save("./pic/" + point + ".png")
        x = pt[0]+15
        y = pt[1]+15
    if max_val > threshold:
        return (x, y)
    else:
        return 0

def locateme(threshold, map):
    # traceimg = cv2.imread("./pic/trace.png")
    "start matching"
    result = invariantMatchTemplate(map, arrow, "TM_SQDIFF_NORMED", threshold, [0,360], 10, True)
    if len(result) == 0:
        print("location not found")
        return 0
    else:
        loc, deg, prob = result[0]
        x = loc[0] + 5
        y = loc[1] + 5
        print("location at (" + str(x) + "," + str(y) + ")")
        # traceimg = cv2.circle(traceimg, (x , y), radius=3, color=(0, 0, 255), thickness=-1)
        # cv2.imwrite("./pic/trace.png", traceimg)
        return (x, y)


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
    print(name + '\t' + str(center))
    return center


def escapeBuying(window):
    # if a ship is researched, escape buying via the item shop
    screenshot()
    click(getButtonLocation("researchdone"))
    time.sleep(3)
    getScreen(PATH)
    if hasImage("newshipresearched", 0.91, None) and not hasImage("partsdone", 0.91, None):
        screenshot()
        click(getButtonLocation("shop"))
        screenshot()
        click(getButtonLocation("itemshop"))
        screenshot()
        spamESC(3)
    partsDone(window)


def partsDone(window):
    time.sleep(1)
    screenshot()
    if hasImage("autoresearch", 0.92, None):
        click(getButtonLocation("autoresearch"))
        time.sleep(10)
        spamESC(15)

def startScript():
    # start the whole script
    detectWindow()

def getmap():
    img = Image.open(PATH)
    left = 1480
    top = 660
    right = 1900
    bottom = 1060
    img = img.crop((left, top, right, bottom))
    img.save(MAP)
    return img

def getbigmap():
    img = Image.open(PATH)
    left = 954
    top = 251
    right = 1703
    bottom = 1000
    img = img.crop((left, top, right, bottom))
    img.save(MAPBIG)
    return img

def getPointLocation(map):
    global pointAloc, pointBloc, pointCloc
    pointAloc = locatePoint("A", 0.89, map)
    pointBloc = locatePoint("B", 0.89, map)
    pointCloc = locatePoint("C", 0.89, map)
    if not type(pointAloc) is int:
        print("有A点，在" + str(pointAloc))
    else:
        print("没有A点")
    if not type(pointBloc) is int:
        print("有B点，在" + str(pointBloc))
    else:
        print("没有B点")
    if not type(pointCloc) is int:
        print("有C点，在" + str(pointCloc))
    else:
        print("没有C点")

def testactivity(window):
    global captureMode
    if not captureMode:
        getmap()
        time.sleep(0.01)
        map = cv2.imread(MAP)
        # getPointLocation(map)
        time.sleep(0.01)
        loc = locateme(0.70, map)
        if not type(loc) is int:
            pix = test_cord.load()
            current = pix[loc[0], loc[1]]
            print(str(current))
            if current == (255, 0, 0):
                keyboard.release('w')
                pressWithDelay('d', 0.6, 0.5)
                print("right!")
                keyboard.press('w')
            elif current == (0, 255, 0):
                keyboard.release('w')
                pressWithDelay('`', 0.3, 0)
                print("stop!")
            elif current == (0, 0, 255):
                keyboard.release('w')
                pressWithDelay('a', 0.6, 0.5)
                print("left!")
                keyboard.press('w')
            else:
                keyboard.press('w')
        else:
            keyboard.press('w')
    else:
        while hasImage("specmode", 0.98, None) or not hasImage("person", 0.92, None):
            screenshot()
            time.sleep(5)
        cap = getmap()
        i = 1
        time.sleep(1)
        while i < 1500:
            temppath = './model/route/map' + str(i) + '.png'
            if not os.path.isfile(temppath):
                print("截图！")
                cap.save(temppath)
                break
            else:
                if checkforrepeats(temppath, 0.50):
                    print("和"+str(i)+"个一样呢")
                    break
                i = i + 1
        time.sleep(0.5)
        while window.title.__contains__("战"):
            time.sleep(5)
        print("下一局")


def battleactivity(window, windowName):
    screenshot()
    while not hasImage("specmode", 0.97, None):
        screenshot()
        time.sleep(0.5)
    time.sleep(0.5)
    pressWithDelay("enter", 0.3, 0.3)
    while not hasImage("person", 0.92, None):
        screenshot()
        time.sleep(0.5)
    log("加入战斗")
    time.sleep(0.5)
    i = 1
    thismap = getmap()
    route = None
    mostlikly = -1
    biggest = -1
    while i < 150:
        temppath = './model/route/map' + str(i) + '.png'
        if not os.path.isfile(temppath):
            break
        else:
            passed, score = checkforrepeats(temppath, 0.50)
            if passed:
                if score > biggest:
                    biggest = score
                    mostlikly = i
            i = i + 1
    if mostlikly == -1:
        log("出现了没见过的地图")
        thismap.save('./model/route/map' + str(i) + '.png')
    else:
        log("地图应该是：" + str(mostlikly))
        if os.path.isfile("./model/route/route/route" + str(mostlikly) + ".png"):
            route = Image.open("./model/route/route/route" + str(mostlikly) + ".png")
    screenshot()
    while windowName.__contains__("战"):
        i = i + 1
        if i < 300:
            windowName = window.title
            getmap()
            time.sleep(0.01)
            map = cv2.imread(MAP)
            time.sleep(0.01)
            loc = locateme(0.65, map)
            if type(loc) is not int and route is not None:
                pix = route.load()
                current = pix[loc[0], loc[1]]
                if current == (255, 0, 0):
                    keyboard.release('w')
                    pressWithDelay('d', 0.6, 0.1)
                    pressWithDelay('w', 0.5, 0.1)
                    keyboard.press('w')
                    time.sleep(0.5)
                elif current == (0, 255, 0):
                    keyboard.release('w')
                    pressWithDelay('`', 0.5, 0)
                    # print("stop!")
                elif current == (0, 0, 255):
                    keyboard.release('w')
                    pressWithDelay('a', 0.6, 0.1)
                    pressWithDelay('w', 0.5, 0.1)
                    keyboard.press('w')
                elif current == (255, 0, 255):
                    keyboard.release('w')
                    pressWithDelay('j', 8, 5)
                else:
                    keyboard.press('w')
            else:
                keyboard.press('w')
        screenshot()
        if i > 300:
            # Game is stuck, try to escape
            log("检测到卡死")
            keyboard.release('w')
            screenshot()
            time.sleep(10)
        if hasImage("crates", 0.95, None):
            # unlocked crates
            log("出了个箱子，记得查看背包")
            screenshot()
            time.sleep(10)
            pressWithDelay('esc', 0.1, 0.5)
            break
        if hasImage("specmode", 0.97, None):
            log("刚刚好像没进游戏，再进一次")
            pressWithDelay('enter', 0.1, 4)
        if hasImage("youdied", 0.95, None):
            # died before the game ended
            log("已死亡，返回主界面中，\n为防止网络情况卡死，等待10秒")
            getScreen(PATH)
            time.sleep(1)
            while hasImage("youdied", 0.94, None):
                click(getButtonLocation("youdied"))
                getScreen(PATH)
                time.sleep(1)
            time.sleep(10)
            break
    # game is over\
    keyboard.release('w')
    log("结束战斗，等待结算")
    # wait for the points
    time.sleep(10)
    getScreen(PATH)
    time.sleep(0.5)
    researchDone = False
    i = 0
    while not hasImage("gotobase", 0.97, None):
        i = i + 1
        if i > 30:
            log("检测到卡死")
            timeoutEscape()
            break
        time.sleep(0.5)
        getScreen(PATH)
        time.sleep(0.5)
        if hasImage("crates", 0.95, None):
            # unlocked crates
            log("===出了个箱子，记得查看背包===")
            getScreen(PATH)
            time.sleep(15)
            pressWithDelay('esc', 0.1, 0.5)
        if hasImage("researchdone", 0.98, None):
            # new ship got researched. To avoid spending all SL, we glitch the research out
            researchDone = True
            log("===解锁了配件或新车===")
            time.sleep(5)
            saveResults(window, 150)
            escapeBuying(window)
            break
        if hasImage("exitout", 0.91, None):
            click(getButtonLocation("exitout"))
    if not researchDone:
        saveResults(window, 150)
        getScreen(PATH)
        time.sleep(0.5)
        log("结算完成，返回主界面")
        click(getButtonLocation("gotobase"))
        getScreen(PATH)
        time.sleep(0.5)
        if hasImage("newshipresearched", 0.97, None) or hasImage("autoresearch", 0.97, None):
            # new ship got researched. To avoid spending all SL, we glitch the research out
            log("===解锁了配件或新车===")
            escapeBuying(window)
    time.sleep(1)
    getScreen(PATH)


def WTScript(window):
    getScreen(PATH)
    windowName = window.title
    # print(windowName)
    if not (windowName.__contains__("试") or windowName.__contains__("战") or windowName.__contains__("载")):
        # We are at the hanger. Have to enter a game first
        if hasImage("enterbattle", 0.95, None) or hasImage("enterbattle2", 0.95, None):
            pyautogui.moveTo(500, 500)
            time.sleep(0.01)
            click(getButtonLocation("enterbattle"))
            screenshot()
            if hasImage("downloadprompt", 0.97, None):
                # If the texture download happens to be there, close it
                click(getButtonLocation("downloadprompt"))
                screenshot()
                if hasImage("exitout", 0.92, None):
                    click(getButtonLocation(("exitout")))
                    screenshot()
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
        testactivity(window)
    elif windowName.__contains__("载"):
        # We are loading into one game
        time.sleep(4)
    elif windowName.__contains__("战"):
        # We are currently in a game
        global captureMode
        if captureMode:
            testactivity(window)
        else:
            battleactivity(window, windowName)



if __name__ == '__main__':
    isRunning = False
    window = sg.Window(title="蓝莓派陆战助手", layout=layout)
    app = threading.Thread(target=startScript, daemon=True)
    while True:
        event, values = window.read()
        # End program if user closes window or
        # presses the OK button
        if event == "停止并退出" or event == sg.WIN_CLOSED:
            f.close()
            sys.exit()
        if event == "开始" and not isRunning:
            isRunning = True
            log("开始运行")
            app.start()
        if event == "截图" and not isRunning:
            isRunning = True
            captureMode = True
            app.start()



