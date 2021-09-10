# Oxi 08/09/2021

import math
import tkinter as tk
import tkinter.filedialog
from tkinter import ttk
from time import sleep
import time
import os

window = tk.Tk()
window.title("TKinter Physics Sim - V1")
window.geometry("1000x1000")

canvas = tk.Canvas(window, width=1000, height=975)
canvas.pack()

# ------------[SETTINGS]------------
# Physics
gravity = 0.004 # DEFAULT: 0.002
numIterations = 1 # "Stiffness" (Will impact performance)

# Display
circleRadius = 5
stickThickness = 3
# ------------[SETTINGS]------------

# ------------[DATA]------------
leftMouseDown = False
rightMouseDown = False
mouseX = 0
mouseY = 0
lastFrameTime = 0
prevPoint = 0
simNow = False
currentTempStick = 0
shiftHeld = False
heldPoint = 0
grabPoint = 0
pauseSim = True
statusBar = 0
statusText = "Ready"
canClick = False
gridX=8
gridY=8
windowCollide = True
# ------------[DATA]------------

# ------------[GUI DATA]------------
grav=0
iters=0
gridx=0
gridy=0
simparampopup=0
gridparampopup=0
controlsPopup=0
menubar=0
# ------------[GUI DATA]------------

# ------------[STORAGE]------------
pointsBeforeSim = []
sticksBeforeSim = []
points = []
sticks = []
# ------------[STORAGE]------------

# ------------[VECTOR MATH FUNCTIONS]------------
def Distance2D(pos1, pos2):
    return math.sqrt(((pos2[0]-pos1[0])**2)+((pos2[1]-pos1[1])**2))

def Add2D(pos1, pos2):
    return [pos1[0] + pos2[0], pos1[1] + pos2[1]]

def Subtract2D(pos1, pos2):
    return [pos1[0] - pos2[0], pos1[1] - pos2[1]]

def Divide2D(pos1, pos2):
    return [pos1[0]/pos2[0], pos1[1]/pos2[1]]

def Divide2DByFloat(vect, flt):
    return [vect[0]/flt, vect[1]/flt]

def Multiply2DByFloat(vect, flt):
    return [vect[0]*flt, vect[1]*flt]

def Length2D(vect):
    return math.sqrt((vect[0] * vect[0]) + (vect[1] * vect[1]))

def Normalize2D(vect):
    length = Length2D(vect)
    return [vect[0]/length, vect[1]/length]
# ------------[VECTOR MATH FUNCTIONS]------------

# ------------[CLASSES]------------
class Point(object):
    def __init__(self, pos, tlocked, render=True, join=True):
        global canvas, circleRadius, points
        self.position = pos
        self.previousPosition = pos
        self.locked = tlocked
        self.references = []

        colour = "black"
        if tlocked:
            colour = "pink"

        if render:
            self.renderObject = canvas.create_oval(pos[0]-circleRadius, pos[1]-circleRadius, pos[0]+circleRadius, pos[1]+circleRadius, fill=colour)
            canvas.tag_raise(self.renderObject)
            if join:
                points.append(self)

    def ToggleLock(self):
        global canvas
        self.locked = not self.locked

        colour = "black"
        if self.locked:
            colour = "pink"
        
        canvas.itemconfigure(self.renderObject, fill=colour)

    def Remove(self):
        global canvas, points

        if hasattr(self, 'renderObject'):
            canvas.delete(self.renderObject)
        refIndex = 0
        referencesCopy = self.references.copy()
        while refIndex < len(referencesCopy):
            referencesCopy[refIndex].Remove()
            refIndex+=1

        if self in points:
            points.remove(self)

    def Parse(self):
        txt = ""
        dataCache = [self.position[0], self.position[1], int(self.locked)]
        for data in dataCache:
            txt += str(data)+ ","
        return txt[:-1]

class Stick:
    def __init__(self, tpointA, tpointB, tlength, tbackground, render=True):
        global canvas, sticks, stickThickness
        self.pointA = tpointA
        self.pointB = tpointB
        self.pointA.references.append(self)
        self.pointB.references.append(self)
        self.length = tlength

        colour = "black"
        if tbackground:
            colour = "gray89"

        self.background = tbackground

        if render:
            self.renderObject = canvas.create_line(self.pointA.position[0], self.pointA.position[1], self.pointB.position[0], self.pointB.position[1], width=stickThickness, fill=colour)
            canvas.tag_lower(self.renderObject)

        sticks.append(self)

    def Remove(self):
        global canvas, sticks
        
        if hasattr(self, 'renderObject'):
            canvas.delete(self.renderObject)
        if self in self.pointA.references:
            self.pointA.references.remove(self)
        if self in self.pointB.references:
            self.pointB.references.remove(self)
        sticks.remove(self)

    def Parse(self):
        global points
        txt = ""
        dataCache = [points.index(self.pointA), points.index(self.pointB), self.length, int(self.background)]
        for data in dataCache:
            txt += str(data) + ","
        return txt[:-1]

class StandInStick():
    def __init__(self, tpointA, tpointB, tlength, tbackground):
        self.pointA = tpointA
        self.pointB = tpointB
        self.length = tlength
        self.background = tbackground

class TempStick:
    def __init__(self, tpointA, mousePos, tbackground):
        global canvas, sticks, currentTempStick, stickThickness
        self.pointA = tpointA

        colour = "black"
        if tbackground:
            colour = "gray89"
            
        self.background = tbackground
        self.renderObject = canvas.create_line(self.pointA.position[0], self.pointA.position[1], mousePos[0], mousePos[1], width=stickThickness, fill=colour)
        currentTempStick = self

    def Cleanup(self):
        global currentTempStick, canvas
        canvas.delete(currentTempStick.renderObject)
        currentTempStick = 0
        
# ------------[CLASSES]------------

# ------------[UTIL FUNCTIONS]------------
def GetClosestPoint(pos):
    global points
    
    closest = 0
    closestDist = 1000000
    for point in points:
        if Distance2D(pos, point.position) < closestDist:
            closest = point
            closestDist = Distance2D(pos, point.position)

    return closest

def GetClosestPointThreshold(pos, thresh):
    global points
    
    closest = 0
    closestDist = 1000000
    for point in points:
        if Distance2D(pos, point.position) < closestDist and Distance2D(pos, point.position) < thresh:
            closest = point
            closestDist = Distance2D(pos, point.position)

    return closest

def Clear(overrideClick=False):
    global statusText, canClick

    if canClick or overrideClick:
        canClick = False
        statusText = "Clearing"
        for point in points:
            point.Remove()

        sleep(0.1)

        for point in points:
            canvas.delete(point.renderObject)

        points.clear()

        for stick in sticks:
                stick.Remove()

        sleep(0.1)

        for stick in sticks:
            canvas.delete(stick.renderObject)

        sticks.clear()
        statusText = "Ready"
        canClick = True

def Clamp(val, mn, mx):
    if val > mx:
        val = mx
    if val < mn:
        val = mn
    return val

def CalculateMainCenter(width, height):
    global window
    x = window.winfo_x() + (window.winfo_width()/2) - (width/2)
    y = window.winfo_y() + (window.winfo_height()/2) - (height/2)
    return [x, y]

def ToggleWindowCollision():
    global windowCollide
    windowCollide = not windowCollide
    
# ------------[UTIL FUNCTIONS]------------

# ------------[INPUT HANDLERS]------------
def Mouse1DownHandler(event):
    global leftMouseDown, window, prevPoint, heldPoint, simNow, grabPoint, canClick

    if not leftMouseDown and canClick:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        closest = GetClosestPointThreshold([mouseX, mouseY], circleRadius * 5) 
        if closest == 0:
            newPoint = Point([mouseX, mouseY], False)
            prevPoint = newPoint
        else:
            if closest.locked == True or simNow == False: 
                heldPoint = closest
            elif simNow == True:
                grabPoint = Point([mouseX, mouseY], True, False, False)
                Stick(grabPoint, closest, Distance2D(grabPoint.position, closest.position), False, False)
    
    leftMouseDown = True

def Mouse1UpHandler(event):
    global leftMouseDown, heldPoint, grabPoint, canClick

    if canClick:
        if simNow == False and not heldPoint == 0:
            refIndex = 0
            referencesCopy = heldPoint.references.copy()
            while refIndex < len(referencesCopy):
                referencesCopy[refIndex].length = Distance2D(referencesCopy[refIndex].pointA.position, referencesCopy[refIndex].pointB.position)
                refIndex += 1

        if not grabPoint == 0:
            grabPoint.Remove()
            grabPoint = 0
    
    heldPoint = 0
    leftMouseDown = False

def Mouse2DownHandler(event, shift=False):
    global rightMouseDown, window, prevPoint, shiftHeld, canClick

    if not rightMouseDown and canClick:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        closest = GetClosestPoint([mouseX, mouseY])
        TempStick(closest, [mouseX, mouseY], shift)
        
    rightMouseDown = True

def Mouse2UpHandler(event, shift=False):
    global rightMouseDown, currentTempStick, shiftHeld, canClick
    
    if canClick:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        closest = GetClosestPoint([mouseX, mouseY])
        if not closest == currentTempStick.pointA:
            newStick = Stick(currentTempStick.pointA, closest, Distance2D(currentTempStick.pointA.position, closest.position), currentTempStick.background)

    currentTempStick.Cleanup()
        
    rightMouseDown = False

def ShiftDownHandler(event):
    Mouse2DownHandler(event, True)

def ShiftUpHandler(event):
    Mouse2UpHandler(event, True)

# ----[SIMULATION RESET]----
def SpaceHandler(event=None):
    # WORST FUNCTION. I had to just keep adding random clears and stuff for it to actually clear. I dont know why though because the point class isnt printing or showing errors. This works for now i guess...

    global canClick
    if canClick:
        global simNow, pointsBeforeSim, points, sticksBeforeSim, sticks, canvas, pauseSim, statusText
        simNow = not simNow
        pauseSim = False
        if simNow:
            statusText = "Simulating"
            
            pointsBeforeSim.clear()

            pointIndex = 0
            while pointIndex < len(points):
                pointsBeforeSim.append(Point(points[pointIndex].position, points[pointIndex].locked, False))
                pointIndex +=1

            sticksBeforeSim.clear()
            
            stickIndex = 0
            while stickIndex < len(sticks):
                sticksBeforeSim.append(StandInStick(points.index(sticks[stickIndex].pointA), points.index(sticks[stickIndex].pointB), sticks[stickIndex].length, sticks[stickIndex].background))
                stickIndex += 1
        else:
            canClick = False
            statusText = "Restoring"
            Render()
            
            for point in points:
                point.Remove()

            sleep(0.1)

            for point in points:
                canvas.delete(point.renderObject)

            points.clear()

            for stick in sticks:
                stick.Remove()

            sleep(0.1)

            for stick in sticks:
                canvas.delete(stick.renderObject)

            sticks.clear()
            
            pointBeforeIndex = 0
            while pointBeforeIndex < len(pointsBeforeSim):
                points.append(Point(pointsBeforeSim[pointBeforeIndex].position, pointsBeforeSim[pointBeforeIndex].locked, True, False))
                pointBeforeIndex += 1
                statusText = "Restoring " + str(pointBeforeIndex) + "/" + str(len(pointsBeforeSim) + len(sticksBeforeSim))
                Render()
            
            stickBeforeIndex = 0
            while stickBeforeIndex < len(sticksBeforeSim):
                Stick(points[sticksBeforeSim[stickBeforeIndex].pointA], points[sticksBeforeSim[stickBeforeIndex].pointB], sticksBeforeSim[stickBeforeIndex].length, sticksBeforeSim[stickBeforeIndex].background)
                stickBeforeIndex += 1
                statusText = "Restoring " + str(stickBeforeIndex + len(pointsBeforeSim)) + "/" + str(len(sticksBeforeSim) + len(pointsBeforeSim))
                Render()

            statusText = "Ready"
            canClick = True
# ----[SIMULATION RESET]-----

def LockHandler(event):
    global canClick
    if canClick:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        closest = GetClosestPoint([mouseX, mouseY])
        closest.ToggleLock()

def DeleteHandler(event):
    global heldPoint, canClick

    if canClick:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        closest = GetClosestPoint([mouseX, mouseY])
        heldPoint = 0
        closest.Remove()

def GridSpawnHandler(event):
    global canClick
    if canClick:
        canClick = False
        #Spawns a connected grid
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        previousYPoints = []
        xIndex = 0
        for xIndex in range(gridX):
            currentYPoints = []
            yIndex = 0
            for yIndex in range(gridY):
                currentYPoints.append(Point([mouseX + (xIndex*60), mouseY + (yIndex*60)], False))
                Render()
                if not yIndex == 0:
                    Stick(currentYPoints[yIndex], currentYPoints[yIndex-1], Distance2D(currentYPoints[yIndex].position, currentYPoints[yIndex-1].position), False)
                    Render()
                if not xIndex == 0:
                    Stick(currentYPoints[yIndex], previousYPoints[yIndex], Distance2D(currentYPoints[yIndex].position, previousYPoints[yIndex].position), False)
                    Render()
            previousYPoints = currentYPoints.copy()
            currentYPoints.clear()
        canClick = True

def PauseHandler(event):
    global pauseSim, simNow, statusText, canClick

    if canClick:
        if simNow:
            pauseSim = not pauseSim
            if pauseSim:
                statusText = "Paused"
            else:
                statusText = "Simulating"
    
# ------------[INPUT HANDLERS]------------

# ------------[LOADING]------------
def SaveToFile(event=None):
    global simNow, points, sticks, statusText, canClick, gravity, numIterations
    
    if canClick: 
        if not simNow:
            canClick = False
            path = os.getcwd()+'/Maps/'
            if not os.path.exists(path):
                os.mkdir(path)
            file = tk.filedialog.asksaveasfile(mode="w", filetypes=[('phys', '*.phys')], defaultextension=[('*.phys')], initialdir=path)

            if file:
                statusText = "Saving"
                data = []
                for point in points:
                    data.append(point.Parse()+'\n')

                data.append('=\n')

                for stick in sticks:
                    data.append(stick.Parse()+'\n')

                data.append('=\n')

                data.append(str(gravity) + "," + str(numIterations))
                
                file.writelines(data)
                file.close()
                statusText = "Ready"
            canClick = True

def LoadFromFile(event=None):
    global points, sticks, simNow, pauseSim, statusText, canClick, gravity, numIterations

    if canClick:
        simNow = False
        pauseSim = False
        canClick = False

        Clear(True)

        path = os.getcwd()+'/Maps/'
        if not os.path.exists(path):
            os.mkdir(path)
        file = tk.filedialog.askopenfile(mode="r", filetypes=[('phys', '*.phys')], defaultextension=[('*.phys')], initialdir=path)
        if file:
            statusText = "Loading"
            
            data = file.read()
            segments = data.split('=')
            pointList = segments[0].split('\n')
            stickList = segments[1].split('\n')
            total = len(pointList) + len(stickList)
            for pointDataChunk in pointList:
                pointData = pointDataChunk.split(',')
                #print(pointData)
                if len(pointData) == 3:
                    Point([int(pointData[0]), int(pointData[1])], bool(int(pointData[2])))
                statusText = "Loading " + str(pointList.index(pointDataChunk)) + "/" + str(total)
                Render()
                
            for stickDataChunk in stickList:
                stickData = stickDataChunk.split(',')
                #print(stickData)
                if len(stickData) == 4:
                    Stick(points[int(stickData[0])], points[int(stickData[1])], float(stickData[2]), bool(int(stickData[3])))
                statusText = "Loading " + str(stickList.index(stickDataChunk)+len(pointList)) + "/" + str(total)
                Render()

            settings = segments[2].split(',')
            gravity = float(settings[0])
            numIterations = int(settings[1])

            canClick = True
            statusText = "Ready"
            
# ------------[LOADING]------------

# ------------[BINDS]------------
window.bind("<ButtonPress-1>", Mouse1DownHandler)
window.bind("<ButtonRelease-1>", Mouse1UpHandler)
window.bind("<ButtonPress-3>", Mouse2DownHandler)
window.bind("<ButtonRelease-3>", Mouse2UpHandler)
window.bind("<space>", SpaceHandler)
window.bind("<Return>", LockHandler)
window.bind("<Delete>", DeleteHandler)
window.bind("g", GridSpawnHandler)
window.bind("p", PauseHandler)
window.bind("<Shift-ButtonPress-3>", ShiftDownHandler)
window.bind("<Shift-ButtonRelease-3>", ShiftUpHandler)
window.bind("<Control-s>", SaveToFile)
window.bind("<Control-o>", LoadFromFile)
# ------------[BINDS]------------

# ------------[SIMULATION]------------
def Simulate():
    global points, lastFrameTime, numIterations, windowCollide
    
    for point in points:
        if not point.locked:
            posBefore = point.position

            # Keep velocity from last update
            posdelta = Subtract2D(point.position, point.previousPosition)
            point.position = Add2D(point.position, posdelta)
            
            # Calculate frame delta time
            delta = (time.time()*1000)-lastFrameTime

            # Simulate Gravity based upon frame time
            point.position[1] += gravity * delta * delta

            # Window Collision
            if windowCollide:
                point.position[0] = Clamp(point.position[0], 10, 990)

                if point.position[1] > 970:
                    point.position = Subtract2D(point.position, Divide2DByFloat(posdelta, 3))
                point.position[1] = Clamp(point.position[1], 10, 970)
            
            point.previousPosition = posBefore

    # Run through iterations to get physics to settle
    for i in range(numIterations):
        
        for stick in sticks:

            # Calculate stick data
            stickCenter = Divide2DByFloat(Add2D(stick.pointA.position, stick.pointB.position), 2)
            stickDir = Normalize2D(Subtract2D(stick.pointA.position, stick.pointB.position))
            
            if not stick.pointA.locked:
                # Push point A to be restrained by stick length
                stick.pointA.position = Add2D(stickCenter, Multiply2DByFloat(stickDir, stick.length/2))
            if not stick.pointB.locked:
                # Push point B to be restrained by stick length
                stick.pointB.position = Subtract2D(stickCenter, Multiply2DByFloat(stickDir, stick.length/2))
                
# ------------[SIMULATION]------------

# ------------[INTERACT]------------
def Interact():
    global heldPoint, grabPoint

    if not heldPoint == 0:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        heldPoint.position = [mouseX, mouseY]

    if not grabPoint == 0:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        grabPoint.position = [mouseX, mouseY]
        
# ------------[INTERACT]------------
    
# ------------[RENDER]------------
def Render():
    global canvas, fpsText, lastFrameTime, currentTempStick, statusBar, statusText

    # Update each point and stick's location

    for stick in sticks:
        if hasattr(stick, 'renderObject'):
            canvas.coords(stick.renderObject, stick.pointA.position[0], stick.pointA.position[1], stick.pointB.position[0], stick.pointB.position[1])
        
    for point in points:
        canvas.coords(point.renderObject, point.position[0]-circleRadius, point.position[1]-circleRadius, point.position[0]+circleRadius, point.position[1]+circleRadius)


    # Update Statusbar
    statusBar['text'] = statusText
    
    # Update temp stick if it exists
    if not currentTempStick == 0:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        canvas.coords(currentTempStick.renderObject, currentTempStick.pointA.position[0], currentTempStick.pointA.position[1], mouseX, mouseY)

    # Update FPS Counter
    canvas.itemconfigure(fpsText, text=str(math.floor((1/((time.time()*1000)-lastFrameTime))*1000)))

    # Draw
    window.update()
    
# ------------[RENDER]------------

# ------------[POPUP FUNCTIONS]------------
def SimParamsEnter():
    global grav, iters, gravity, numIterations, simparampopup, canClick
    
    canClick = True
    try:
        simparampopup.destroy()
        gravity = float(grav.get())
        numIterations = int(iters.get())
    except Exception as e: print(e)

def GridParamsEnter():
    global grav, gridx, gridy, gridX, gridY, gridparampopup, canClick
    
    canClick = True
    try:
        gridparampopup.destroy()
        gridX = int(gridx.get())
        gridY = int(gridy.get())
    except Exception as e: print(e)

def SimParamsGravDefault():
    global grav, gravity
    grav.set('0.004')
    gravity = 0.004

def SimParamsNumItersDefault():
    global iters, numIterations
    iters.set('1')
    numIterations = 1

def ControlsLoseFocus(event):
    global controlsPopup
    controlsPopup.focus_force()
    
# ------------[POPUP FUNCTIONS]------------

# ------------[POPUPS]------------
def InfoWindow():
    global window
    popup = tk.Tk()
    popup.resizable(False, False)
    center = CalculateMainCenter(260, 100)
    
    popup.geometry('%dx%d+%d+%d' % (260, 100, center[0], center[1]))
    popup.wm_title("About")
    label = ttk.Label(popup, text="TKinter-based Physics Simulator. Written by Oxi.")
    label.pack(side="top", fill="x", pady=20)
    B1 = ttk.Button(popup, text="Okay", command = popup.destroy)
    B1.pack()

def SimParamsWindow():
    global window, gravity, numIterations, grav, iters, simparampopup

    simparampopup = tk.Tk()
    simparampopup.resizable(False, False)
    #popup.overrideredirect(True)
    
    width=215
    height=80
    center = CalculateMainCenter(width, height)
    
    simparampopup.geometry('%dx%d+%d+%d' % (width, height, center[0], center[1]))
    simparampopup.wm_title("Sim Params")


    grav = tk.StringVar(simparampopup, value=str(gravity))
    iters = tk.StringVar(simparampopup, value=str(numIterations))

    tk.Label(simparampopup, text="Gravity:").grid(row=0, column=0)
    tk.Label(simparampopup, text="Iterations:").grid(row=1, column=0)

    tk.Entry(simparampopup, textvariable=grav).grid(row=0, column=1)
    tk.Entry(simparampopup, textvariable=iters).grid(row=1, column=1)

    gravButton = ttk.Button(simparampopup, text="<", command=SimParamsGravDefault, width=3)
    gravButton.grid(row=0, column=2)

    itersButton = ttk.Button(simparampopup, text="<", command=SimParamsNumItersDefault, width=3)
    itersButton.grid(row=1, column=2)

    button = ttk.Button(simparampopup, text="Save", command=SimParamsEnter)
    button.grid(row=3, column=1)

    simparampopup.protocol('WM_DELETE_WINDOW', SimParamsEnter)

def GridParamsWindow():
    global window, gridx, gridy, gridX, gridY, gridparampopup

    gridparampopup = tk.Tk()
    gridparampopup.resizable(False, False)
    #popup.overrideredirect(True)
    
    width=215
    height=60
    center = CalculateMainCenter(width, height)
    
    gridparampopup.geometry('%dx%d+%d+%d' % (width, height, center[0], center[1]))
    gridparampopup.wm_title("Grid Params")


    gridx = tk.StringVar(gridparampopup, value=str(gridX))
    gridy = tk.StringVar(gridparampopup, value=str(gridY))

    tk.Label(gridparampopup, text="Amount:").grid(row=0, column=0)

    tk.Entry(gridparampopup, textvariable=gridx, width=10).grid(row=0, column=1)
    tk.Entry(gridparampopup, textvariable=gridy, width=10).grid(row=0, column=2)

    button = ttk.Button(gridparampopup, text="Save", command=GridParamsEnter)
    button.grid(row=1, column=2)

    gridparampopup.protocol('WM_DELETE_WINDOW', GridParamsEnter)

def ControlsWindow():
    global window, controlsPopup, canClick

    canClick = False

    controlsPopup = tk.Tk()
    controlsPopup.resizable(False, False)
    #controlsPopup.overrideredirect(True)
    
    width=325
    height=330
    center = CalculateMainCenter(width, height)
    
    controlsPopup.geometry('%dx%d+%d+%d' % (width, height, center[0], center[1]))
    controlsPopup.wm_title("Welcome")

    label = tk.Label(controlsPopup, text="TKinter Physics Sim v1 - Written by Oxi \n \n Controls: \n Click in empty space - Spawn Point \n Right click and drag from a point to another - Join Points \n \n Enter while hovering over point - Lock Point \n Delete - Delete closest point \n \n G - Spawn Configurable Grid \n \n Space - Start/Stop Simulation \n P - Pause \n \n CTRL+S - Save \n CTRL+O - Open")
    label.pack(side="top", fill="x", pady=20)

    button = ttk.Button(controlsPopup, text="Continue", command=controlsPopup.destroy)
    button.pack()

    controlsPopup.bind("<FocusOut>", ControlsLoseFocus)
    controlsPopup.attributes("-topmost", True)
    controlsPopup.focus_force()

    canClick = True
    
# ------------[POPUPS]------------

# ------------[GUI MENUBAR]------------
menubar = tk.Menu(window)
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Open", command=LoadFromFile)
filemenu.add_command(label="Save", command=SaveToFile)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=window.destroy)
menubar.add_cascade(label="File", menu=filemenu)

editmenu = tk.Menu(menubar, tearoff=0)
editmenu.add_command(label="Clear", command=Clear)
menubar.add_cascade(label="Edit", menu=editmenu)

simmenu = tk.Menu(menubar, tearoff=0)
simmenu.add_command(label="Start/Stop Simulation", command=SpaceHandler)
menubar.add_cascade(label="Simulation", menu=simmenu)

settingsmenu = tk.Menu(menubar, tearoff=0)
settingsmenu.add_command(label="Simulation Parameters", command=SimParamsWindow)
settingsmenu.add_command(label="Grid Parameters", command=GridParamsWindow)
settingsmenu.add_separator()
settingsmenu.add_command(label="Toggle Window Collision", command=ToggleWindowCollision)
menubar.add_cascade(label="Settings", menu=settingsmenu)

helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="Controls", command=ControlsWindow)
menubar.add_cascade(label="Help", menu=helpmenu)

window.config(menu=menubar)
# ------------[GUI MENUBAR]------------

statusBar = tk.Label(window, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
statusBar.pack(side=tk.BOTTOM, fill=tk.X)

fpsText = canvas.create_text(20, 15, fill="black", text="0")

Render()

ControlsWindow()

# MAIN LOOP
while True:
    if simNow and not pauseSim:
        Simulate()

    Interact()
    Render()

    lastFrameTime = (time.time()*1000)

    sleep(0.01)
# MAIN LOOP
