# Oxi 08/09/2021

import math
import tkinter as tk
import tkinter.filedialog
from tkinter import ttk
from time import sleep
import time
import os
from vector2d import Vector2D
import platform

window = tk.Tk()
window.title("TKinter Physics Sim - V1")
window.geometry("1920x1080")

canvas = tk.Canvas(window, width=1000, height=1000)
canvas.pack(fill="both", expand=True)

def resize(event):
    global canvas
    w,h = event.width, event.height-80
    canvas.config(width=w, height=h)

window.bind('<Configure>', resize)

# ------------[SETTINGS]------------
# Physics
gravity = 2000
numIterations = 2
weakStickStrength = 25

# Display
circleRadius = 5
stickThickness = 3
# ------------[SETTINGS]------------

# ------------[DATA]------------
leftMouseDown = False
rightMouseDown = False
middleMouseDown = False
mouseX = 0
mouseY = 0
lastFrameTime = (time.time())
prevPoint = 0
snapResolution=10
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
currentFile = ""
simColour = True

dragDeleting = False
lastMousePos = Vector2D.Zero()

selectedStick = 0

camPos = Vector2D.Zero()
camScale = 1
# ------------[DATA]------------

# ------------[GUI DATA]------------
grav=0
iters=0
weakstrength=0
snapresolution=0
gridx=0
gridy=0
simparampopup=0
gridparampopup=0
snapparampopup=0
controlsPopup=0
savepromptpopup=0
savepromptreturn=None
menubar=0
# ------------[GUI DATA]------------

# ------------[STORAGE]------------
pointsBeforeSim = []
objectPointsBeforeSim = []
sticksBeforeSim = []
points = []
objectPoints = []
sticks = []
# ------------[STORAGE]------------

# ------------[CLASSES]------------
class Point(object):
    def __init__(self, pos, tlocked, render=True, join=True, tsave=True):
        global canvas, circleRadius, points, camPos
        self.position = Point.SnapPosition(pos)
        self.previousPosition = Point.SnapPosition(pos)
        self.locked = tlocked
        self.references = []
        self.save = tsave

        colour = "black"
        if tlocked:
            colour = "pink"

        if render:
            self.renderObject = canvas.create_oval(self.position.x-circleRadius-camPos.x, self.position.y-circleRadius-camPos.y, self.position.x+circleRadius-camPos.x, self.position.y+circleRadius-camPos.y, fill=colour)
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
        dataCache = [self.position.x, self.position.y, int(self.locked)]
        for data in dataCache:
            txt += str(data)+ ","
        return txt[:-1]

    @staticmethod
    def SnapPosition(targetLoc):
        global snapResolution
        return (targetLoc//snapResolution) * snapResolution

    def Simulate(self):
        global gravity, windowCollide, camPos

        if not self.locked:
            # Store previous position
            posBefore = self.position

            # Keep velocity from last update
            posdelta = (self.position - self.previousPosition)
            self.position = self.position + posdelta

            # Calculate frame delta time
            delta = max((time.time())-lastFrameTime, 1/120)

            # Simulate Gravity based upon frame time
            self.position.y += gravity * delta * delta

            # Check for Window Collision enabled
            if windowCollide and len(self.references) == 0:
                
                # Clamp positions to window bounds
                self.position.x = Clamp(self.position.x, 10+camPos.x, window.winfo_width()-10+camPos.x)
                self.position.y = Clamp(self.position.y, 10+camPos.y, window.winfo_height()-30+camPos.y)
                

            # Apply drag if on window floor
            self.position -= (posdelta / 3) * float(self.position.y > window.winfo_height()-30+camPos.y) * float(windowCollide)

            # Assign posBefore to previous position cache
            self.previousPosition = posBefore

class ObjectPoint(Point):
    def __init__(self, pos, tlocked, render=True, join=True, tsave=True, towner=None, tnewSpawned=False):
        global canvas, circleRadius, points
        self.position = pos
        self.previousPosition = pos
        self.locked = tlocked
        self.references = []
        self.owner = towner
        self.save = tsave
        self.newlySpawned=tnewSpawned

        colour = "red"

        if render:
            self.renderObject = canvas.create_oval(pos.x-circleRadius, pos.y-circleRadius, pos.x+circleRadius, pos.y+circleRadius, fill=colour)
            canvas.tag_raise(self.renderObject)
            if join:
                objectPoints.append(self)

    def Remove(self, skipRefs=False):
        global canvas, objectPoints

        if hasattr(self, 'renderObject'):
            canvas.delete(self.renderObject)

        if not skipRefs:
            refIndex = 0
            referencesCopy = self.references.copy()
            while refIndex < len(referencesCopy):
                referencesCopy[refIndex].Remove()
                refIndex+=1

        if not skipRefs:
            if hasattr(self, 'owner'):
                if self.owner:
                    self.owner.Remove()

        if self in objectPoints:
            objectPoints.remove(self)

    def Parse(self):
        global sticks
        txt = ""
        dataCache = [self.position.x, self.position.y, int(self.locked), sticks.index(self.owner)]
        for data in dataCache:
            txt += str(data)+ ","
        return txt[:-1]

class Stick:
    def __init__(self, tpointA, tpointB, tlength, tbackground, render=True, standin=False, tsave=True, tstickType=0):
        global canvas, sticks, stickThickness, camPos
        self.pointA = tpointA
        self.pointB = tpointB

        self.save = tsave

        self.stickType = tstickType

        if not standin:
            self.pointA.references.append(self)
            self.pointB.references.append(self)

        self.length = tlength
        self.background = tbackground

        colour = self.CalcColour()

        if not standin:
            if render:
                self.renderObject = canvas.create_line(self.pointA.position.x - camPos.x, self.pointA.position.y - camPos.y, self.pointB.position.x - camPos.x, self.pointB.position.y - camPos.y, width=stickThickness, fill=colour)
                canvas.tag_lower(self.renderObject)

            sticks.append(self)

    def CalcColour(self):
        colour = "black"
        if self.background:
            colour = "gray89"
        return colour

    def Remove(self):
        global canvas, sticks

        if hasattr(self, 'renderObject'):
            canvas.delete(self.renderObject)
        if self in self.pointA.references:
            self.pointA.references.remove(self)
        if self in self.pointB.references:
            self.pointB.references.remove(self)
        if self in sticks:
            sticks.remove(self)

    def Parse(self):
        global points, objectPoints
        txt = ""
        dataCache = [(points+objectPoints).index(self.pointA), (points+objectPoints).index(self.pointB), self.length, int(self.background)]
        for data in dataCache:
            txt += str(data) + ","
        return txt[:-1]

    def Simulate(self, onlyClamp=False):
        global windowCollide, camPos

        # onlyClamp means if the stick should not apply constraints, and only clamp the point to the window
        
        # Calculate stick data
        if not onlyClamp:
            stickCenter = (self.pointA.position + self.pointB.position) / 2
            stickDir = (self.pointA.position - self.pointB.position).getNormalised()

        # If pointA is not a fixed point
        if not self.pointA.locked:
            
            # Set pointA's position to where the stick expects it to be.
            if not onlyClamp:
                self.pointA.position = stickCenter + (stickDir * self.length/2)

            # Clamp pointA to the window bounds
            if windowCollide:
                self.pointA.position.x = Clamp(self.pointA.position.x, 10+camPos.x, window.winfo_width()-10+camPos.x)
                self.pointA.position.y = Clamp(self.pointA.position.y, 10+camPos.y, window.winfo_height()-30+camPos.y)

        # If pointB is not a fixed point 
        if not self.pointB.locked:
            
            # Set pointB's position to where the stick expects it to be.
            if not onlyClamp:
                self.pointB.position = stickCenter - (stickDir * (self.length/2))

            # Clamp pointB to the window bounds
            if windowCollide:
                self.pointB.position.x = Clamp(self.pointB.position.x, 10+camPos.x, window.winfo_width()-10+camPos.x)
                self.pointB.position.y = Clamp(self.pointB.position.y, 10+camPos.y, window.winfo_height()-30+camPos.y)


class WeakStick(Stick):
    def CalcColour(self):
        return "Green"

    def Break(self):
        # stickA + (normalize(stickB-stickA) * ((Distance(stickA, stickB)/2)+-10)
        dist = Vector2D.Distance(self.pointA.position, self.pointB.position)/ 2
        stickDir = ((self.pointB.position / self.pointA.position)).getNormalised()

        newPoint = Point((self.pointA.position + (stickDir * (dist-10))), False)
        Stick(self.pointA, newPoint, Vector2D.Distance(self.pointA.position, newPoint.position), False)
        newPoint = Point((self.pointA.position + (stickDir * (dist+10))), False)
        Stick(self.pointB, newPoint, Vector2D.Distance(self.pointB.position, newPoint.position), False)
        self.Remove()


    def Simulate(self):
        global weakStickStrength     
        super().Simulate()

        if Vector2D.Distance(self.pointA.position, self.pointB.position) > self.length + weakStickStrength:
            self.Break()

        if Vector2D.Distance(self.pointA.position, self.pointB.position) < self.length - weakStickStrength:
            self.Break()


class RopeStick(Stick):
    def CalcColour(self):
        if Vector2D.Distance(self.pointA.position, self.pointB.position) > self.length and simColour:
            return "Blue"
        else:
            return "Purple"

    def Simulate(self):
        global canvas

        if hasattr(self, 'renderObject'):
            canvas.itemconfig(self.renderObject, fill=self.CalcColour())

        currentLength = Vector2D.Distance(self.pointA.position, self.pointB.position)
        super().Simulate(not currentLength > self.length)

class SpringyStick(Stick):
    def Simulate(self, onlyClamp=False):
        global windowCollide, camPos

        # onlyClamp means if the stick should not apply constraints, and only clamp the point to the window

        spring = 0.2
        
        # Calculate stick data
        if not onlyClamp:
            stickCenter = (self.pointA.position + self.pointB.position) / 2
            stickDir = (self.pointA.position - self.pointB.position).getNormalised()

        # If pointA is not a fixed point
        if not self.pointA.locked:
            
            # Set pointA's position to where the stick expects it to be.
            if not onlyClamp:
                self.pointA.position = Vector2D.Lerp(self.pointA.position, stickCenter + (stickDir * self.length/2), spring)

            # Clamp pointA to the window bounds
            if windowCollide:
                self.pointA.position.x = Clamp(self.pointA.position.x, 10+camPos.x, window.winfo_width()-10+camPos.x)
                self.pointA.position.y = Clamp(self.pointA.position.y, 10+camPos.y, window.winfo_height()-30+camPos.y)

        # If pointB is not a fixed point 
        if not self.pointB.locked:
            
            # Set pointB's position to where the stick expects it to be.
            if not onlyClamp:
                self.pointB.position = Vector2D.Lerp(self.pointB.position, stickCenter - (stickDir * self.length/2), spring)

            # Clamp pointB to the window bounds
            if windowCollide:
                self.pointB.position.x = Clamp(self.pointB.position.x, 10+camPos.x, window.winfo_width()-10+camPos.x)
                self.pointB.position.y = Clamp(self.pointB.position.y, 10+camPos.y, window.winfo_height()-30+camPos.y)


class SlideStick(Stick):
    def __init__(self, tpointA, tpointB, tlength, tbackground, render=True):
        global canvas, sticks, stickThickness

        self.middlePoint = ObjectPoint((((tpointA.position + tpointB.position) / 2)).AsInt(), False, True, True, True)
        self.stick1 = RopeStick(tpointA, self.middlePoint, tlength, False, True, False, False)
        self.stick2 = RopeStick(tpointB, self.middlePoint, tlength, False, True, False, False)

        self.save = True

        self.pointA = tpointA
        self.pointB = tpointB
        self.length = tlength
        self.background = tbackground

        self.middlePoint.owner = self

        self.pointA.references.append(self)
        self.pointB.references.append(self)
        self.middlePoint.references.append(self)

        sticks.append(self)

    def Simulate(self):
        newDist = Vector2D.Distance(self.pointA.position, self.pointB.position)
        self.stick1.length = newDist-10
        self.stick2.length = newDist-10

        self.stick1.Simulate()
        self.stick2.Simulate()

        middlePointVect = (self.middlePoint.position - self.pointA.position)
        stickVect = (self.pointA.position - self.pointB.position)

        # Project
        projected = Vector2D.Project(middlePointVect, stickVect)

        # middlePoint = pointA + projected
        self.middlePoint.position = (self.pointA.position + projected)

        super().Simulate()

    def Remove(self):
        global canvas, sticks

        if hasattr(self, 'renderObject'):
            canvas.delete(self.renderObject)
        if self in self.pointA.references:
            self.pointA.references.remove(self)
        if self in self.pointB.references:
            self.pointB.references.remove(self)
        if self in self.middlePoint.references:
            self.middlePoint.references.remove(self)
        self.middlePoint.owner = None
        self.middlePoint.Remove()
        self.stick1.Remove()
        self.stick2.Remove()
        if self in sticks:
            sticks.remove(self)

    def ChangeMiddlePoint(self, point):
        oldPoint = self.middlePoint
        self.middlePoint = point
        self.stick1.pointB = point
        self.stick2.pointB = point
        point.owner = self
        if self in oldPoint.references:
            oldPoint.references.remove(self)
        oldPoint.owner = None
        oldPoint.Remove(True)

    def CalcMiddlePoint(self):
        self.middlePoint.position = (((self.pointA.position + self.pointB.position) / 2)).AsInt()

class TempStick:
    def __init__(self, tpointA, mousePos, tbackground, ttype):
        global canvas, sticks, currentTempStick, stickThickness, camPos
        self.pointA = tpointA

        colour = "black"
        if tbackground:
            colour = "gray89"
        if ttype == 1:
            colour = "purple"

        self.background = tbackground
        self.renderObject = canvas.create_line(self.pointA.position.x - camPos.x, self.pointA.position.y - camPos.y, mousePos.x, mousePos.y, width=stickThickness, fill=colour)
        currentTempStick = self

    def Cleanup(self):
        global currentTempStick, canvas
        canvas.delete(currentTempStick.renderObject)
        currentTempStick = 0

# ------------[CLASSES]------------

# ------------[UTIL FUNCTIONS]------------
def GetClosestPoint(pos):
    global points, objectPoints, camPos

    closest = 0
    closestDist = 1000000
    for point in points:
        if Vector2D.Distance(pos, point.position - camPos) < closestDist:
            closest = point
            closestDist = Vector2D.Distance(pos, point.position - camPos)
    for point in objectPoints:
        if Vector2D.Distance(pos, point.position - camPos) < closestDist:
            closest = point
            closestDist = Vector2D.Distance(pos, point.position - camPos)

    return closest

def GetClosestPointThreshold(pos, thresh):
    global points, objectPoints

    closest = 0
    closestDist = 1000000
    for point in points:
        if Vector2D.Distance(pos, point.position - camPos) < closestDist and Vector2D.Distance(pos, point.position - camPos) < thresh:
            closest = point
            closestDist = Vector2D.Distance(pos, point.position - camPos)
    for point in objectPoints:
        if Vector2D.Distance(pos, point.position - camPos) < closestDist and Vector2D.Distance(pos, point.position - camPos) < thresh:
            closest = point
            closestDist = Vector2D.Distance(pos, point.position - camPos)

    return closest

def Clear(overrideClick=False):
    global statusText, canClick, camPos

    if canClick or overrideClick:
        canClick = False
        statusText = "Clearing"
        for point in points:
            point.Remove()

        sleep(0.1)

        camPos = Vector2D.Zero()

        for point in points:
            canvas.delete(point.renderObject)

        for point in objectPoints:
            canvas.delete(point.renderObject)

        points.clear()
        objectPoints.clear()

        for stick in sticks:
                stick.Remove()

        sleep(0.1)

        for stick in sticks:
            if hasattr(stick, 'renderObject'):
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
    return Vector2D(x,y)

def ToggleWindowCollision():
    global windowCollide
    windowCollide = not windowCollide

def StickType(stick):
    typ = 0
    if stick.__class__.__name__ == 'RopeStick':
        typ = 1
    if stick.__class__.__name__ == 'SlideStick':
        typ = 2
    if stick.__class__.__name__ == 'WeakStick':
        typ = 3
    if stick.__class__.__name__ == 'SpringyStick':
        typ = 4
    return typ

def StickTypeClass(classNum):
    stickClass = None
    if classNum == 0:
        stickClass = Stick
    elif classNum == 1:
        stickClass = RopeStick
    elif classNum == 2:
        stickClass = SlideStick
    elif classNum == 3:
        stickClass = WeakStick
    elif classNum == 4:
        stickClass = SpringyStick
    return stickClass

def StickTypeName(num):
    stickName = ""
    if num == 0:
        stickName = "Fixed"
    elif num == 1:
        stickName = "Rope"
    elif num == 2:
        stickName = "Slide"
    elif num == 3:
        stickName = "Weak"
    elif num == 4:
        stickName = "Springy"
    return stickName

def PointType(point):
    typ = 0
    if point.__class__.__name__ == 'ObjectPoint':
        typ = 1
    return typ

def PointTypeClass(classNum):
    pointClass = None
    if classNum == 0:
        pointClass = Point
    elif classNum == 1:
        pointClass = ObjectPoint
    return pointClass

# ------------[UTIL FUNCTIONS]------------

# ------------[INPUT HANDLERS]------------
def Mouse1DownHandler(event):
    global leftMouseDown, window, prevPoint, heldPoint, simNow, grabPoint, canClick, camPos

    if not leftMouseDown and canClick:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        closest = GetClosestPointThreshold(Vector2D(mouseX,mouseY), circleRadius * 5)
        if closest == 0:
            newPoint = Point(Vector2D(mouseX + camPos.x, mouseY + camPos.y), False)
            prevPoint = newPoint
        else:
            if closest.locked == True or simNow == False:
                heldPoint = closest
            elif simNow == True:
                grabPoint = Point(Vector2D(mouseX + camPos.x, mouseY + camPos.y), True, False, False)
                Stick(grabPoint, closest, Vector2D.Distance(grabPoint.position, closest.position), False, False)

    leftMouseDown = True

def Mouse1UpHandler(event):
    global leftMouseDown, heldPoint, grabPoint, canClick

    if canClick:
        if simNow == False and not heldPoint == 0:
            heldPoint.previousPosition = heldPoint.position

            refIndex = 0
            referencesCopy = heldPoint.references.copy()
            while refIndex < len(referencesCopy):
                referencesCopy[refIndex].length = Vector2D.Distance(referencesCopy[refIndex].pointA.position, referencesCopy[refIndex].pointB.position)
                refIndex += 1

        if not grabPoint == 0:
            grabPoint.Remove()
            grabPoint = 0

    heldPoint = 0
    leftMouseDown = False

def Mouse2DownHandler(event, shift=False, alt=False):
    global rightMouseDown, window, prevPoint, shiftHeld, canClick, selectedStick, dragDeleting, lastMousePos

    stickType = 0
    if shift:
        stickType = 1

    if not rightMouseDown and canClick and not alt:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        closest = GetClosestPoint(Vector2D(mouseX,mouseY))
        TempStick(closest, Vector2D(mouseX,mouseY), shift, selectedStick)
    
    if not rightMouseDown and canClick and alt:
        dragDeleting = True

        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        lastMousePos = Vector2D(mouseX,mouseY)

    rightMouseDown = True

def Mouse2UpHandler(event, shift=False, alt=False):
    global rightMouseDown, currentTempStick, shiftHeld, canClick, dragDeleting

    if canClick:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        closest = GetClosestPoint(Vector2D(mouseX,mouseY))
        if currentTempStick:
            if not closest == currentTempStick.pointA:
                stickClass = None
                stickClass = StickTypeClass(selectedStick)
                newStick = stickClass(currentTempStick.pointA, closest, Vector2D.Distance(currentTempStick.pointA.position, closest.position), currentTempStick.background)
        

    dragDeleting = False

    if currentTempStick:
        currentTempStick.Cleanup()

    rightMouseDown = False

def MiddleMouseDownHandler(event):
    global middleMouseDown, lastMousePos
    middleMouseDown = True

    mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
    mouseY = int(window.winfo_pointery()-window.winfo_rooty())
    lastMousePos = Vector2D(mouseX,mouseY)

def MiddleMouseUpHandler(event):
    global middleMouseDown
    middleMouseDown = False

def ShiftDownHandler(event):
    Mouse2DownHandler(event, True)

def ShiftUpHandler(event):
    Mouse2UpHandler(event, True)

def AltDownHandler(event):
    Mouse2DownHandler(event, False, True)

def AltUpHandler(event):
    Mouse2UpHandler(event, False, True)

# ----[SIMULATION RESET]----
def SpaceHandler(event=None):
    # WORST FUNCTION. I had to just keep adding random clears and stuff for it to actually clear. I dont know why though because the point class isnt printing or showing errors. This works for now i guess...

    global canClick
    if canClick:
        global simNow, pauseSim, pointsBeforeSim, points, sticksBeforeSim, sticks, canvas, pauseSim, statusText, objectPointsBeforeSim, objectPoints
        simNow = not simNow
        pauseSim = False
        if simNow:
            statusText = "Simulating"

            pointsBeforeSim.clear()

            pointIndex = 0
            while pointIndex < len(points):
                if points[pointIndex].save:
                    pointsBeforeSim.append(Point(points[pointIndex].position, points[pointIndex].locked, False))
                pointIndex +=1

            sticksBeforeSim.clear()

            stickIndex = 0
            while stickIndex < len(sticks):
                if sticks[stickIndex].save:
                    stickType = StickType(sticks[stickIndex])

                    pointAIndex = (points+objectPoints).index(sticks[stickIndex].pointA)

                    pointBIndex = (points+objectPoints).index(sticks[stickIndex].pointB)

                    sticksBeforeSim.append(Stick(pointAIndex, pointBIndex, sticks[stickIndex].length, sticks[stickIndex].background, False, True, False, stickType))
                stickIndex += 1

            objectPointsBeforeSim.clear()

            objectPointIndex = 0
            while objectPointIndex < len(objectPoints):
                if objectPoints[objectPointIndex].save:
                    objectPoint = objectPoints[objectPointIndex]
                    objectPointsBeforeSim.append(ObjectPoint(objectPoint.position, objectPoint.locked, False, False, False, sticks.index(objectPoint.owner)))
                objectPointIndex += 1

        else:
            if not pauseSim:
                canClick = False
                statusText = "Restoring"
                Render()
                Clear(True)

                pointBeforeIndex = 0
                while pointBeforeIndex < len(pointsBeforeSim):
                    points.append(Point(pointsBeforeSim[pointBeforeIndex].position, pointsBeforeSim[pointBeforeIndex].locked, True, False))
                    pointBeforeIndex += 1
                    percent = ((pointBeforeIndex) / (len(pointsBeforeSim) + len(sticksBeforeSim) + len(objectPointsBeforeSim)))*100
                    statusText = "Restoring " + str(int(percent)) + "%"
                    statusBar['text'] = statusText
                    window.update()


                objectPointBeforeIndex = 0
                while objectPointBeforeIndex < len(objectPointsBeforeSim):
                    objectPoint = objectPointsBeforeSim[objectPointBeforeIndex]
                    newObjectPoint = ObjectPoint(objectPoint.position, objectPoint.locked, True, True, True, objectPoint.owner, True)
                    objectPointBeforeIndex += 1
                    percent = ((len(pointsBeforeSim) + objectPointBeforeIndex) / (len(pointsBeforeSim) + len(sticksBeforeSim) + len(objectPointsBeforeSim)))*100
                    statusText = "Restoring " + str(int(percent)) + "%"
                    statusBar['text'] = statusText
                    window.update()

                stickBeforeIndex = 0
                while stickBeforeIndex < len(sticksBeforeSim):
                    stickClass = None
                    stickType = sticksBeforeSim[stickBeforeIndex].stickType
                    stickClass = StickTypeClass(stickType)
                    combined = points+objectPoints
                    stickClass(combined[sticksBeforeSim[stickBeforeIndex].pointA], combined[sticksBeforeSim[stickBeforeIndex].pointB], sticksBeforeSim[stickBeforeIndex].length, sticksBeforeSim[stickBeforeIndex].background)
                    stickBeforeIndex += 1
                    percent = ((stickBeforeIndex + len(pointsBeforeSim) + len(objectPointsBeforeSim)) / (len(pointsBeforeSim) + len(sticksBeforeSim) + len(objectPointsBeforeSim)))*100
                    statusText = "Restoring " + str(int(percent)) + "%"
                    statusBar['text'] = statusText
                    window.update()

                for objectPoint in objectPoints:
                    if objectPoint.newlySpawned == True:
                        sticks[objectPoint.owner].ChangeMiddlePoint(objectPoint)
                        objectPoint.newlySpawned = False

                statusText = "Ready"
                canClick = True
# ----[SIMULATION RESET]-----

def LockHandler(event):
    global canClick
    if canClick:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        closest = GetClosestPoint(Vector2D(mouseX,mouseY))
        closest.ToggleLock()

def DeleteHandler(event):
    global heldPoint, canClick

    if canClick:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        closest = GetClosestPoint(Vector2D(mouseX,mouseY))
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
                currentYPoints.append(Point(Vector2D(mouseX + (xIndex*60), mouseY + (yIndex*60)), False))
                Render()
                stickClass = StickTypeClass(selectedStick)
                if not yIndex == 0:
                    stickClass(currentYPoints[yIndex], currentYPoints[yIndex-1], Vector2D.Distance(currentYPoints[yIndex].position, currentYPoints[yIndex-1].position), False)
                    Render()
                if not xIndex == 0:
                    stickClass(currentYPoints[yIndex], previousYPoints[yIndex], Vector2D.Distance(currentYPoints[yIndex].position, previousYPoints[yIndex].position), False)
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

def NewFile(contin=False, prompt=False):
    global currentFile, gravity, numIterations, points
    if not currentFile == "":
        if not contin:
            if prompt:
                SavePrompt(NewFile)
        else:
            Clear()
            currentFile = ""
            gravity = 2000
            numIterations = 2
    else:
        if len(points) > 0:
            if not contin:
                if prompt:
                    SavePrompt(NewFile)
                else:
                    Clear()
                    currentFile = ""
                    gravity = 2000
                    numIterations = 2
        else:
            Clear()
            currentFile = ""
            gravity = 2000
            numIterations = 2

def NewFileInst():
    NewFile(False, True)

def CloseSave(contin=False, prompt=False):
    global currentFile, window
    if not currentFile == "":
        if not contin:
            if prompt:
                SavePrompt(CloseSave)
        else:
            window.destroy()
            os._exit(0)
    else:
        if len(points) > 0:
            if not contin:
                if prompt:
                    SavePrompt(CloseSave)
                else:
                    window.destroy()
                    os._exit(0)
            else:
                window.destroy()
                os._exit(0)
        else:
            window.destroy()
            os._exit(0)

def CloseSaveInst():
    CloseSave(False, True)

# ------------[INPUT HANDLERS]------------

# ------------[LOADING]------------
def SaveToFile(event=None, useCurrent=True, returnFunc=None):
    global simNow, points, sticks, statusText, canClick, gravity, numIterations, currentFile

    if canClick or returnFunc:
        if not simNow:
            canClick = False
            path = os.getcwd()+'/Maps/'
            if not os.path.exists(path):
                os.mkdir(path)

            file = None
            if currentFile == "" or not useCurrent:
                file = tk.filedialog.asksaveasfile(mode="w", filetypes=[('phys', '*.phys')], defaultextension=[('*.phys')], initialdir=path)
            else:
                file = open(currentFile, 'w')

            if file:
                currentFile = file.name
                statusText = "Saving"
                data = []
                for point in points:
                    if point.save:
                        data.append(point.Parse()+'\n')
                        percent = ((points.index(point)) / (len(points) + len(sticks) + len(objectPoints)))*100
                        statusText = "Saving " + str(int(percent)) + "%"
                        Render()

                data.append('=\n')

                for stick in sticks:
                    if stick.save:
                        data.append(stick.Parse()+ ',' + str(StickType(stick)) + '\n')
                        percent = ((sticks.index(stick) + len(points)) / (len(points) + len(sticks) + len(objectPoints)))*100
                        statusText = "Saving " + str(int(percent)) + "%"
                        Render()

                data.append('=\n')

                for objectPoint in objectPoints:
                    if objectPoint.save:
                        data.append(objectPoint.Parse() + '\n')
                        percent = ((objectPoints.index(objectPoint) + len(sticks) + len(points)) / (len(points) + len(sticks) + len(objectPoints)))*100
                        statusText = "Saving " + str(int(percent)) + "%"
                        Render()

                data.append('=\n')

                data.append(str(gravity) + "," + str(numIterations))

                file.writelines(data)
                file.close()

                statusText = "Ready"

                if returnFunc:
                    returnFunc()

            canClick = True

def SaveToFileNoCurrent():
    SaveToFile(None, False)

def LoadFromFile(event=None):
    global points, sticks, simNow, pauseSim, statusText, canClick, gravity, numIterations, currentFile, objectPoints, camPos

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
            currentFile = file.name

            data = file.read()
            segments = data.split('=')
            pointList = segments[0].split('\n')
            stickList = segments[1].split('\n')
            objectPointList = segments[2].split('\n')
            total = len(pointList) + len(stickList) + len(objectPointList)
            for pointDataChunk in pointList:
                pointData = pointDataChunk.split(',')
                #print(pointData)
                if len(pointData) == 3:
                    Point(Vector2D(int(pointData[0]), int(pointData[1])), bool(int(pointData[2])))
                percent = ((pointList.index(pointDataChunk)) / (total))*100
                statusText = "Loading " + str(int(percent)) + "%"
                statusBar['text'] = statusText
                window.update()

            for objectPointDataChunk in objectPointList:
                objectPointData = objectPointDataChunk.split(',')
                if len(objectPointData) >= 3:
                    ObjectPoint(Vector2D(int(objectPointData[0]), int(objectPointData[1])), bool(int(objectPointData[2])), True, True, True, int(objectPointData[3]), True)
                percent = ((objectPointList.index(objectPointDataChunk)+len(pointList)) / (total))*100
                statusText = "Loading " + str(int(percent)) + "%"
                statusBar['text'] = statusText
                window.update()

            for stickDataChunk in stickList:
                stickData = stickDataChunk.split(',')
                #print(stickData)
                if len(stickData) == 5:
                    stickClass = StickTypeClass(int(stickData[4]))
                    combined = points+objectPoints
                    stickClass(combined[int(stickData[0])], combined[int(stickData[1])], float(stickData[2]), bool(int(stickData[3])))
                percent = ((stickList.index(stickDataChunk)+len(pointList)+len(objectPointList)) / (total))*100
                statusText = "Loading " + str(int(percent)) + "%"
                statusBar['text'] = statusText
                window.update()

            for objectPoint in objectPoints:
                if objectPoint.newlySpawned == True:
                    sticks[objectPoint.owner].ChangeMiddlePoint(objectPoint)
                    objectPoint.newlySpawned = False

            settings = segments[3].split(',')
            gravity = float(settings[0])
            numIterations = int(settings[1])

            canClick = True
            statusText = "Ready"

# ------------[LOADING]------------

def SelectStick1(event):
    global selectedStick
    selectedStick = 0

def SelectStick2(event):
    global selectedStick
    selectedStick = 1

def SelectStick3(event):
    global selectedStick
    selectedStick = 2

def SelectStick4(event):
    global selectedStick
    selectedStick = 3

def SelectStick5(event):
    global selectedStick
    selectedStick = 4

# ------------[BINDS]------------

platform.system()
rightClickNum = "3"
altModifier = "Alt"
onMac = False
if platform.system() == 'Darwin':
    rightClickNum = "2"
    altModifier = "Option"
    window.bind("<Control-ButtonPress-2>", MiddleMouseDownHandler)
    window.bind("<Control-ButtonRelease-2>", MiddleMouseUpHandler)
    onMac = True

window.bind("<ButtonPress-1>", Mouse1DownHandler)
window.bind("<ButtonRelease-1>", Mouse1UpHandler)
window.bind("<ButtonPress-" + rightClickNum + ">", Mouse2DownHandler)
window.bind("<ButtonRelease-" + rightClickNum + ">", Mouse2UpHandler)
if not onMac:
    window.bind("<ButtonPress-2>", MiddleMouseDownHandler)
    window.bind("<ButtonRelease-2>", MiddleMouseUpHandler)
window.bind("<space>", SpaceHandler)
window.bind("<Return>", LockHandler)
window.bind("r", DeleteHandler)
window.bind("g", GridSpawnHandler)
window.bind("p", PauseHandler)
window.bind("<Shift-ButtonPress-3>", ShiftDownHandler)
window.bind("<Shift-ButtonRelease-3>", ShiftUpHandler)
window.bind("<" + altModifier + "-ButtonPress-" + rightClickNum + ">", AltDownHandler)
window.bind("<" + altModifier + "-ButtonRelease-" + rightClickNum + ">", AltUpHandler)
window.bind("<Control-s>", SaveToFile)
window.bind("<Control-Shift-s>", SaveToFileNoCurrent)
window.bind("<Control-o>", LoadFromFile)
window.bind("<Control-n>", NewFileInst)

window.bind("1", SelectStick1)
window.bind("2", SelectStick2)
window.bind("3", SelectStick3)
window.bind("4", SelectStick4)
window.bind("5", SelectStick5)
# ------------[BINDS]------------

# ------------[SIMULATION]------------
def Simulate():
    global points, objectPoints, sticks, lastFrameTime, numIterations, windowCollide

    for point in points:
        point.Simulate()

    for point in objectPoints:
        point.Simulate()

    # Run through iterations to get physics to settle
    for i in range(numIterations):
        for stick in sticks:
            stick.Simulate()
# ------------[SIMULATION]------------

# ------------[INTERACT]------------
def Interact():
    global heldPoint, grabPoint, dragDeleting, lastMousePos, camPos

    if not heldPoint == 0:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        heldPoint.position = Point.SnapPosition(Vector2D(mouseX + camPos.x, mouseY + camPos.y))
        if not simNow:
            for ref in heldPoint.references:
                if ref.__class__.__name__ == "SlideStick":
                    ref.CalcMiddlePoint()

    if not grabPoint == 0:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        grabPoint.position = Vector2D(mouseX + camPos.x, mouseY + camPos.y)

    if dragDeleting:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())

        for stick in sticks:
            if Vector2D.isIntersecting(lastMousePos, Vector2D(mouseX,mouseY), (stick.pointA.position - camPos), (stick.pointB.position - camPos)):
                stick.Remove()
        
        lastMousePos = Vector2D(mouseX,mouseY)
    
    if middleMouseDown:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())

        camPos.x += lastMousePos.x - mouseX
        camPos.y += lastMousePos.y - mouseY

        lastMousePos = Vector2D(mouseX,mouseY)

# ------------[INTERACT]------------

# ------------[RENDER]------------
def Render():
    global canvas, fpsText, lastFrameTime, currentTempStick, statusBar, statusText, window, currentFile, objectPoints, sticks, camPos, backgroundDots

    # Update each point and stick's location
    for stick in sticks:
        if hasattr(stick, 'renderObject'):
            canvas.coords(stick.renderObject, stick.pointA.position.x - camPos.x, stick.pointA.position.y - camPos.y, stick.pointB.position.x - camPos.x, stick.pointB.position.y - camPos.y)

    for point in points:
        canvas.coords(point.renderObject, point.position.x-circleRadius - camPos.x, point.position.y-circleRadius - camPos.y, point.position.x+circleRadius - camPos.x, point.position.y+circleRadius - camPos.y)
    for point in objectPoints:
        canvas.coords(point.renderObject, point.position.x-circleRadius - camPos.x, point.position.y-circleRadius - camPos.y, point.position.x+circleRadius - camPos.x, point.position.y+circleRadius - camPos.y)

    # Update Statusbar
    statusBar['text'] = statusText

    # Update temp stick if it exists
    if not currentTempStick == 0:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        canvas.coords(currentTempStick.renderObject, currentTempStick.pointA.position.x - camPos.x, currentTempStick.pointA.position.y - camPos.y, mouseX, mouseY)

    # Update FPS Counter
    canvas.itemconfigure(fpsText, text="FPS: " + str(math.floor((1/(max((time.time())-lastFrameTime,1/120))))) + " - Camera X: " + str(camPos.x) + ", Y: " + str(-camPos.y))

    canvas.itemconfigure(selectedStickText, text="Selected Joint Type (1/2/3/4): " + StickTypeName(selectedStick))

    # Update Title Bar
    title = "TKinter Physics Sim - V1"
    if not currentFile == "":
        title += " - " + currentFile
    window.title(title)

    # Draw
    window.update()

# ------------[RENDER]------------

# ------------[GUI FUNCTIONS]------------
def SimParamsEnter():
    global grav, iters, gravity, numIterations, simparampopup, canClick, weakstrength, weakStickStrength

    canClick = True
    try:
        simparampopup.destroy()
        gravity = float(grav.get())
        numIterations = int(iters.get())
        weakStickStrength = int(weakstrength.get())
    except Exception as e: print(e)

def GridParamsEnter():
    global grav, gridx, gridy, gridX, gridY, gridparampopup, canClick

    canClick = True
    try:
        gridparampopup.destroy()
        gridX = int(gridx.get())
        gridY = int(gridy.get())
    except Exception as e: print(e)

def SnapParamsEnter():
    global snapresolution, snapResolution, canClick, snapparampopup

    canClick = True
    try:
        snapparampopup.destroy()
        snapResolution = int(snapresolution.get())
    except Exception as e: print(e)

def SnapParamsResolutionDefault():
    global snapresolution, snapResolution
    snapresolution.set('1')
    snapResolution = 1

def SimParamsGravDefault():
    global grav, gravity
    grav.set('2000')
    gravity = 2000

def SimParamsNumItersDefault():
    global iters, numIterations
    iters.set('2')
    numIterations = 2

def SimParamsWeakStrengthDefault():
    global weakstrength, weakStickStrength
    weakstrength.set('25')
    weakStickStrength = 25

def ControlsLoseFocus(event):
    global controlsPopup
    controlsPopup.focus_force()

def SavePromptSave():
    global savepromptreturn, savepromptpopup
    savepromptpopup.destroy()
    SaveToFile(None, True, SavePromptSaveFinished)

def SavePromptSaveFinished():
    global savepromptreturn
    SavePrompt(savepromptreturn, True, True)

def SavePromptNoSave():
    global savepromptreturn
    SavePrompt(savepromptreturn, True, True)

def SavePromptCancel():
    global savepromptreturn
    SavePrompt(savepromptreturn, True, False)

# ------------[GUI FUNCTIONS]------------

# ------------[POPUPS]------------
def SavePrompt(returnFunc, returnNow=False, contin=False):
    global savepromptreturn, savepromptpopup, canClick
    savepromptreturn = returnFunc

    if not returnNow:
        canClick = False
        global window
        savepromptpopup = tk.Tk()
        savepromptpopup.resizable(False, False)
        #savepromptpopup.overrideredirect(True)

        width=250
        height=100
        center = CalculateMainCenter(width, height)

        savepromptpopup.geometry('%dx%d+%d+%d' % (width, height, center.x, center.y))
        savepromptpopup.wm_title("Alert")

        label = ttk.Label(savepromptpopup, text="You will lose your work if you dont save!")
        label.pack(side="top", expand=True, fill="none", pady=15)

        save = ttk.Button(savepromptpopup, text="Save", command=SavePromptSave)
        save.pack(side="left", expand=True, fill="none", pady=(0, 5))

        dontsave = ttk.Button(savepromptpopup, text="Don't Save", command=SavePromptNoSave)
        dontsave.pack(side="left", expand=True, fill="none", pady=(0, 5))

        cancel = ttk.Button(savepromptpopup, text="Cancel", command=SavePromptCancel)
        cancel.pack(side="left", expand=True, fill="none", pady=(0, 5))

        savepromptpopup.protocol('WM_DELETE_WINDOW', SavePromptCancel)
    else:
        canClick = True
        returnFunc(contin)

def InfoWindow():
    global window
    popup = tk.Tk()
    popup.resizable(False, False)
    center = CalculateMainCenter(260, 100)

    popup.geometry('%dx%d+%d+%d' % (260, 100, center.x, center.y))
    popup.wm_title("About")
    label = ttk.Label(popup, text="TKinter-based Physics Simulator. Written by Oxi.")
    label.pack(side="top", fill="x", pady=20)
    B1 = ttk.Button(popup, text="Okay", command = popup.destroy)
    B1.pack()

def SnapParamsWindow():
    global window, snapparampopup, snapresolution, snapResolution

    snapparampopup = tk.Tk()
    snapparampopup.resizable(False, False)
    #popup.overrideredirect(True)

    width=215
    height=60
    center = CalculateMainCenter(width, height)

    snapparampopup.geometry('%dx%d+%d+%d' % (width, height, center.x, center.y))
    snapparampopup.wm_title("Snap Params")

    snapresolution = tk.StringVar(snapparampopup, value=str(snapResolution))

    tk.Label(snapparampopup, text="Grid Size:").grid(row=0, column=0)

    tk.Entry(snapparampopup, textvariable=snapresolution, width=10).grid(row=0, column=1)

    resolutionButton = ttk.Button(snapparampopup, text="<", command=SnapParamsResolutionDefault, width=3)
    resolutionButton.grid(row=0, column=2)

    button = ttk.Button(snapparampopup, text="Save", command=SnapParamsEnter)
    button.grid(row=1, column=2)

    snapparampopup.protocol('WM_DELETE_WINDOW', SnapParamsEnter)

def SimParamsWindow():
    global window, gravity, numIterations, grav, iters, simparampopup, weakstrength, weakStickStength

    simparampopup = tk.Tk()
    simparampopup.resizable(False, False)
    #popup.overrideredirect(True)

    width=300
    height=100
    center = CalculateMainCenter(width, height)

    simparampopup.geometry('%dx%d+%d+%d' % (width, height, center.x, center.y))
    simparampopup.wm_title("Sim Params")


    grav = tk.StringVar(simparampopup, value=str(gravity))
    iters = tk.StringVar(simparampopup, value=str(numIterations))
    weakstrength = tk.StringVar(simparampopup, value=str(weakStickStrength))

    tk.Label(simparampopup, text="Gravity:").grid(row=0, column=0)
    tk.Label(simparampopup, text="Iterations:").grid(row=1, column=0)
    tk.Label(simparampopup, text="Weak-Stick Max Stretch:").grid(row=2, column=0)

    tk.Entry(simparampopup, textvariable=grav).grid(row=0, column=1)
    tk.Entry(simparampopup, textvariable=iters).grid(row=1, column=1)
    tk.Entry(simparampopup, textvariable=weakstrength).grid(row=2, column=1)

    gravButton = ttk.Button(simparampopup, text="<", command=SimParamsGravDefault, width=3)
    gravButton.grid(row=0, column=2)

    itersButton = ttk.Button(simparampopup, text="<", command=SimParamsNumItersDefault, width=3)
    itersButton.grid(row=1, column=2)

    strengthButton = ttk.Button(simparampopup, text="<", command=SimParamsWeakStrengthDefault, width=3)
    strengthButton.grid(row=2, column=2)

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

    gridparampopup.geometry('%dx%d+%d+%d' % (width, height, center.x, center.y))
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
    height=390
    center = CalculateMainCenter(width, height)

    controlsPopup.geometry('%dx%d+%d+%d' % (width, height, center.x, center.y))
    controlsPopup.wm_title("Welcome")

    label = tk.Label(controlsPopup, text="TKinter Physics Sim v1 - Written by Oxi \n \n Controls: \n Click in empty space - Spawn Point \n Right click and drag from a point to another - Join Points \n \n Enter while hovering over point - Lock Point \n \n 1/2/3/4 - Select join type \n\n R - Delete closest point \n Alt + Right Click Drag - Slice joints \n \n G - Spawn Configurable Grid \n \n Space - Start/Stop Simulation \n P - Pause \n \n CTRL+S - Save \n CTRL+O - Open")
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
filemenu.add_command(label="New", command=NewFileInst)
filemenu.add_separator()
filemenu.add_command(label="Open", command=LoadFromFile)
filemenu.add_separator()
filemenu.add_command(label="Save", command=SaveToFile)
filemenu.add_command(label="Save As..", command=SaveToFileNoCurrent)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=CloseSaveInst)
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
settingsmenu.add_command(label="Snap Parameters", command=SnapParamsWindow)
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

fpsText = canvas.create_text(15, 15, fill="black", text="0", anchor="w")
selectedStickText = canvas.create_text(15, 33, fill="black", text="Current Stick: ", anchor="w")

Render()

ControlsWindow()

window.protocol('WM_DELETE_WINDOW', CloseSaveInst)
lastFrameTime = (time.time())

# MAIN LOOP
while True:
    startRenderTime = time.time()
    
    if simNow and not pauseSim:
        Simulate()

    Interact()
    Render()

    # Target 120 fps. If update took longer, remove from delay time, so frames stay consistent
    frameTime = (time.time() - startRenderTime)
    sleepTime = max(0, (1/120) - frameTime)
    
    lastFrameTime = (time.time())

    sleep(sleepTime)
# MAIN LOOP
