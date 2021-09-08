# Oxi 08/09/2021

import math
import tkinter as tk
from time import sleep
import time

window = tk.Tk()
window.title("Rope Physics Solver - Written by Oxi - GUI WIP")
window.geometry("1000x1000")

canvas = tk.Canvas(window, width=1000, height=1000)
canvas.pack()

print("Rope/Cloth Solver - Written by Oxi - GUI coming soon")
print("")
print("Controls:")
print("Click in empty space - Spawn Point")
print("Right click and drag off of one point onto another - Join Points")
print("")
print("Enter while hovering over point - Lock Point")
print("Delete - Delete closest Point")
print("")
print("G - Spawn grid")
print("")
print("Space - Start/Stop Simulation")

# ------------[SETTINGS]------------
# Physics
gravity = 0.002 # DEFAULT: 0.002
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
# ------------[DATA]------------

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

        try:
            canvas.delete(self.renderObject)
            refIndex = 0
            referencesCopy = self.references.copy()
            while refIndex < len(referencesCopy):
                referencesCopy[refIndex].Remove()
                refIndex+=1
            points.remove(self)
        except Exception as e: print(e)

class Stick:
    def __init__(self, tpointA, tpointB, tlength, render=True):
        global canvas, sticks, stickThickness
        self.pointA = tpointA
        self.pointB = tpointB
        self.pointA.references.append(self)
        self.pointB.references.append(self)
        self.length = tlength

        if render:
            self.renderObject = canvas.create_line(self.pointA.position[0], self.pointA.position[1], self.pointB.position[0], self.pointB.position[1], width=stickThickness)
            sticks.append(self)

    def Remove(self):
        global canvas, sticks
        canvas.delete(self.renderObject)
        if self in self.pointA.references:
            self.pointA.references.remove(self)
        if self in self.pointB.references:
            self.pointB.references.remove(self)
        sticks.remove(self)

class StandInStick():
    def __init__(self, tpointA, tpointB, tlength):
        self.pointA = tpointA
        self.pointB = tpointB
        self.length = tlength

class TempStick:
    def __init__(self, tpointA, mousePos):
        global canvas, sticks, currentTempStick, stickThickness
        self.pointA = tpointA
        self.renderObject = canvas.create_line(self.pointA.position[0], self.pointA.position[1], mousePos[0], mousePos[1], width=stickThickness)
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
# ------------[UTIL FUNCTIONS]------------

# ------------[INPUT HANDLERS]------------
def Mouse1DownHandler(event):
    global leftMouseDown, window, prevPoint

    if not leftMouseDown:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        newPoint = Point([mouseX, mouseY], False)

        prevPoint = newPoint
    
    leftMouseDown = True

def Mouse1UpHandler(event):
    global leftMouseDown
    leftMouseDown = False

def Mouse2DownHandler(event):
    global rightMouseDown, window, prevPoint

    if not rightMouseDown:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        closest = GetClosestPoint([mouseX, mouseY])
        TempStick(closest, [mouseX, mouseY])
        
    rightMouseDown = True

def Mouse2UpHandler(event):
    global rightMouseDown, currentTempStick

    mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
    mouseY = int(window.winfo_pointery()-window.winfo_rooty())
    closest = GetClosestPoint([mouseX, mouseY])
    if not closest == currentTempStick.pointA:
        newStick = Stick(currentTempStick.pointA, closest, Distance2D(currentTempStick.pointA.position, closest.position))

    currentTempStick.Cleanup()
        
    rightMouseDown = False

# ----[SIMULATION RESET]----
def SpaceHandler(event):
    # WORST FUNCTION. I had to just keep adding random clears and stuff for it to actually clear. I dont know why though because the point class isnt printing or showing errors. This works for now i guess...
    
    global simNow, pointsBeforeSim, points, sticksBeforeSim, sticks, canvas
    simNow = not simNow
    if simNow:
        pointsBeforeSim.clear()

        pointIndex = 0
        while pointIndex < len(points):
            pointsBeforeSim.append(Point(points[pointIndex].position, points[pointIndex].locked, False))
            pointIndex +=1

        sticksBeforeSim.clear()
        
        stickIndex = 0
        while stickIndex < len(sticks):
            sticksBeforeSim.append(StandInStick(points.index(sticks[stickIndex].pointA), points.index(sticks[stickIndex].pointB), sticks[stickIndex].length))
            stickIndex += 1
    else:
        for point in points:
            point.Remove()

        sleep(0.1)

        for point in points:
            canvas.delete(point.renderObject)

        points.clear()
        
        pointBeforeIndex = 0
        while pointBeforeIndex < len(pointsBeforeSim):
            points.append(Point(pointsBeforeSim[pointBeforeIndex].position, pointsBeforeSim[pointBeforeIndex].locked, True, False))
            pointBeforeIndex += 1

        for stick in sticks:
            stick.Remove()

        sleep(0.1)

        for stick in sticks:
            canvas.delete(stick.renderObject)

        sticks.clear()
        
        stickBeforeIndex = 0
        while stickBeforeIndex < len(sticksBeforeSim):
            Stick(points[sticksBeforeSim[stickBeforeIndex].pointA], points[sticksBeforeSim[stickBeforeIndex].pointB], sticksBeforeSim[stickBeforeIndex].length)
            stickBeforeIndex += 1
# ----[SIMULATION RESET]-----

def LockHandler(event):
    mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
    mouseY = int(window.winfo_pointery()-window.winfo_rooty())
    closest = GetClosestPoint([mouseX, mouseY])
    closest.ToggleLock()

def DeleteHandler(event):
    mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
    mouseY = int(window.winfo_pointery()-window.winfo_rooty())
    closest = GetClosestPoint([mouseX, mouseY])
    closest.Remove()

def GridSpawnHandler(event):
    #Spawns a connected grid
    mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
    mouseY = int(window.winfo_pointery()-window.winfo_rooty())
    previousYPoints = []
    xIndex = 0
    for xIndex in range(8):
        currentYPoints = []
        yIndex = 0
        for yIndex in range(8):
            currentYPoints.append(Point([mouseX + (xIndex*75), mouseY + (yIndex*75)], False))
            if not yIndex == 0:
                Stick(currentYPoints[yIndex], currentYPoints[yIndex-1], Distance2D(currentYPoints[yIndex].position, currentYPoints[yIndex-1].position))
            if not xIndex == 0:
                Stick(currentYPoints[yIndex], previousYPoints[yIndex], Distance2D(currentYPoints[yIndex].position, previousYPoints[yIndex].position))
        previousYPoints = currentYPoints.copy()
        currentYPoints.clear()
        
    
# ------------[INPUT HANDLERS]------------

# ------------[BINDS]------------
window.bind("<ButtonPress-1>", Mouse1DownHandler)
window.bind("<ButtonRelease-1>", Mouse1UpHandler)
window.bind("<ButtonPress-3>", Mouse2DownHandler)
window.bind("<ButtonRelease-3>", Mouse2UpHandler)
window.bind("<space>", SpaceHandler)
window.bind("<Return>", LockHandler)
window.bind("<Delete>", DeleteHandler)
window.bind("g", GridSpawnHandler)
# ------------[BINDS]------------

# ------------[SIMULATION]------------
def Simulate():
    global points, lastFrameTime, numIterations
    
    for point in points:
        if not point.locked:
            posBefore = point.position

            # Keep velocity from last update
            point.position = Add2D(point.position, Subtract2D(point.position, point.previousPosition))
            
            # Calculate frame delta time
            delta = (time.time()*1000)-lastFrameTime

            # Simulate Gravity based upon frame time
            point.position[1] += gravity * delta * delta
            
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
    
# ------------[RENDER]------------
def Render():
    global canvas, fpsText, lastFrameTime, currentTempStick

    # Update each point and stick's location
    for point in points:
        canvas.coords(point.renderObject, point.position[0]-circleRadius, point.position[1]-circleRadius, point.position[0]+circleRadius, point.position[1]+circleRadius)

    for stick in sticks:
        canvas.coords(stick.renderObject, stick.pointA.position[0], stick.pointA.position[1], stick.pointB.position[0], stick.pointB.position[1])

    # Update temp stick if it exists
    if not currentTempStick == 0:
        mouseX = int(window.winfo_pointerx()-window.winfo_rootx())
        mouseY = int(window.winfo_pointery()-window.winfo_rooty())
        canvas.coords(currentTempStick.renderObject, currentTempStick.pointA.position[0], currentTempStick.pointA.position[1], mouseX, mouseY)

    # Update FPS Counter
    canvas.itemconfigure(fpsText, text=str(math.floor((1/((time.time()*1000)-lastFrameTime))*1000)))
# ------------[RENDER]------------

# Static Render Object Setup
fpsText = canvas.create_text(20, 15, fill="black", font="Comic 20", text="0")

# MAIN LOOP
while True:
    if simNow:
        Simulate()
    
    Render()

    window.update()

    lastFrameTime = (time.time()*1000)

    sleep(0.01)
# MAIN LOOP

