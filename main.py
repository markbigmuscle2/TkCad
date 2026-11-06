from tkinter import *
from tkinter import ttk
from contextlib import suppress

from canvasTools import *
from customWidgets import *
from changeHistory import *
from geometry import *
from labeledInputs import LabeledInput
from menus import *

root = Tk()
root.geometry("800x600")
root.title("TkCad")
root.state("zoomed")

globalVars = GlobalVariables(root)

GeometryGrid.globalVars = globalVars
Drawing.globalVars = globalVars
Dimension.globalVars = globalVars

Ribbon.globalVars = globalVars
StatusBar.globalVars = globalVars
PropertyMenu.globalVars = globalVars
ToolSettings.globalVars = globalVars

ExportMenu.globalVars = globalVars
DimensionStyleSettings.globalVars = globalVars

HistoryManager.globalVars = globalVars

Tool.globalVars = globalVars
CanvasContextMenu.globalVars = globalVars

LabeledInput.globalVars = globalVars

globalVars.root = root

Drawing.pointRadius = globalVars.pointRadius
Point.pointRadius = globalVars.pointRadius

Drawing.viewOffset = globalVars.viewOffset
Point.viewOffset = globalVars.viewOffset

Drawing.toolActivatedCounter = globalVars.toolActivatedCounter

Drawing.angleIncrement = globalVars.angleIncrement

# menu
MenuBar.globalVars = globalVars
root.config(menu=MenuBar(root))

# other widgets

canvas = Canvas(root, bg="white", bd=2, relief=RIDGE)
Drawing.canvas = canvas
Point.canvas = canvas
Ribbon.canvas = canvas
ExportMenu.canvas = canvas
Dimension.canvas = canvas
Tool.canvas = canvas
FixedTextAnnotation.canvas = canvas

globalVars.fixedTextAnnotation.show()

# grid
grid = GeometryGrid(canvas)
globalVars.grid = grid

propertyMenu = PropertyMenu(root)

Ribbon.propertyMenu = propertyMenu
Tool.propertyMenu = propertyMenu
Command.propertyMenu = propertyMenu

statusBar = StatusBar(root)

toolbar = Ribbon(root)
toolbar.bindGlobalVariables(globalVars)

# canvas context menu

canvasContextMenu = CanvasContextMenu(root)

# conversion

ppi = globalVars.ppi.get()
 
def convertToAbsoluteSize(value=0, unit="px"): 
    if unit == "in":
        return value * ppi
    elif unit == "cm":
        return value * ppi/2.54
    elif unit == "mm":
        return value * ppi/25.4
    return value
    
def convertPx(value=0, unit="px"):
    if unit == "in":
        return value / ppi
    elif unit == "cm":
        return value / (ppi/2.54)
    elif unit == "mm":
        return value / (ppi/25.4)
    return value

# event

## btn 1 events
def btn1Clicked(event):
    toolbar.toolActivated(event)
    
def btn1Down(event):
    toolbar.toolBtn1Down(event)

def btn1Motion(event):
    toolbar.toolBtn1Motion(event)
    
def ctrlBtn1Clicked(event):
    toolbar.toolActivated(event, True)
    
def ctrlBtn1Down(event):
    toolbar.toolBtn1Down(event, True)
    
def ctrlBtn1Motion(event):
    toolbar.toolBtn1Motion(event, True)
    
## right click events

def btn3Clicked(event):
    canvasContextMenu.popup(event.x_root, event.y_root, selection=propertyMenu.selection)

## other events

def deleteKeyPressed(event):
    globalVars.historyManager.do(EraseCommand(drawings=propertyMenu.selection))
    
    for drawing in propertyMenu.selection:
        drawing.delete()
        
    propertyMenu.startSelection()
    
    propertyMenu.clearSelection()
    
    propertyMenu.finishSelection()

def motion(event):
    zoom = globalVars.zoom.get()/100
    
    canvasCursorPos = globalVars.canvasCursorPosition
    canvasCursorPos.set(round(canvas.canvasx(event.x) / zoom), round(canvas.canvasy(event.y) / zoom))

    toolbar.toolMotion(event)
            
def gridChanged(a, b, c):
    grid.generate(offsetX=globalVars.viewOffset.x.get(), offsetY=globalVars.viewOffset.y.get())
    
def propertyMenuVisibilityChanged(a, b, c):
    if globalVars.showPropertyMenu.get():
        propertyMenu.grid(row=3, column=1, sticky="ns")
    else: propertyMenu.grid_forget()
    
def unitChanged(a, b, c):
    gridSize = globalVars.gridSize.get()
    lastUnit = globalVars.lastUnit.get()
    currentUnit = globalVars.unit.get()
    
    gridSize = convertPx(convertToAbsoluteSize(gridSize, lastUnit), currentUnit)
    
    globalVars.lastUnit.set(currentUnit)
    globalVars.gridSize.set(gridSize)
    
    gridChanged(a, b, c)

def configure(event): # canvas size changed
    vX = globalVars.viewOffset.x.get()
    vY = globalVars.viewOffset.y.get()
    grid.generate(offsetX=vX, offsetY=vY)
    
def mouseWheel(event, shift):
    tool = globalVars.tool.get()
    
    vX = globalVars.viewOffset.x.get()
    vY = globalVars.viewOffset.y.get()

    canvas.scan_mark(vX, vY)
   
    if shift: 
        globalVars.viewOffset.set(vX - event.delta, vY)
        canvas.scan_dragto(vX + event.delta, vY, gain=1)
    else: 
        globalVars.viewOffset.set(vX, vY - event.delta)
        canvas.scan_dragto(vX, vY + event.delta, gain=1)

    grid.generate(offsetX=canvas.canvasx(0), offsetY=canvas.canvasy(0))
            
def zoom(event):
    scaleFactor = 1.0
    vX = globalVars.viewOffset.x.get()
    vY = globalVars.viewOffset.y.get()
        
    if event.delta > 0: scaleFactor = 1.1
    elif event.delta < 0: scaleFactor = 1/1.1
    
    globalVars.zoom.set(globalVars.zoom.get() * scaleFactor)
    
    grid.generate(offsetX=canvas.canvasx(0), offsetY=canvas.canvasy(0))
    
    Drawing.redrawAll()
    Dimension.redrawAll()
    
def zoomChanged(*args):
    with suppress(Exception):
        grid.generate(offsetX=canvas.canvasx(0), offsetY=canvas.canvasy(0))
    
        scaleFactor = globalVars.zoom.get() / globalVars.lastZoom.get()
        
        canvas.scale("drawing", 0, 0, scaleFactor, scaleFactor)
        canvas.scale("dimension", 0, 0, scaleFactor, scaleFactor)
        canvas.scale("point", 0, 0, scaleFactor, scaleFactor)
        
        globalVars.lastZoom.set(globalVars.zoom.get())

# binding events
canvas.bind("<Button-1>", btn1Down)
canvas.bind("<ButtonRelease-1>", btn1Clicked)
canvas.bind("<Configure>", configure)
canvas.bind("<B1-Motion>", btn1Motion, add="+")
canvas.bind("<Control-Button-1>", ctrlBtn1Down)
canvas.bind("<Control-B1-Motion>", ctrlBtn1Motion)

canvas.bind("<ButtonRelease-3>", btn3Clicked)

canvas.bind("<Motion>", motion, add="+")
canvas.bind("<MouseWheel>", lambda event: mouseWheel(event, False))
canvas.bind("<Shift-MouseWheel>", lambda event: mouseWheel(event, True))
canvas.bind("<Control-MouseWheel>", zoom)

globalVars.gridSize.trace_add("write", gridChanged)
globalVars.showGrid.trace_add("write", gridChanged)
globalVars.showPropertyMenu.trace_add("write", propertyMenuVisibilityChanged)
globalVars.unit.trace_add("write", unitChanged)
globalVars.zoom.trace_add("write", zoomChanged)

root.bind("<Control-z>", globalVars.historyManager.undo)
root.bind("<Control-y>", globalVars.historyManager.redo)

root.bind("<Delete>", deleteKeyPressed)

# layout
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(3, weight=1)

root.grid_propagate(False)

ttk.Separator(root).grid(row=0, column=0, columnspan=2, sticky="nsew")

toolbar.grid(row=1, column=0, columnspan=2, sticky="nsew")

ttk.Separator(root).grid(row=2, column=0, columnspan=2, sticky="nsew")

canvas.grid(row=3, column=0, sticky="nsew")
if globalVars.showPropertyMenu.get(): propertyMenu.grid(row=3, column=1, sticky="ns")

ttk.Separator(root).grid(row=4, column=0, columnspan=2, sticky="nsew")

statusBar.grid(row=5, column=0, columnspan=2, sticky="w")

ttk.Separator(root).grid(row=6, column=0, columnspan=2, sticky="nsew")

globalVars.fixedTextAnnotation.bindGlobalVars(globalVars)

# mainloop

root.mainloop()