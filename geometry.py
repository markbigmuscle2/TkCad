from customWidgets import *
from changeHistory import DrawCommand
from conversions import Conversions

from decimal import Decimal
from propertyData import *
from tkinter import font, IntVar, StringVar

#import changeHistory

import math
import numpy as np
import re

convertToAbsoluteSize = Conversions.convertToAbsoluteSize
convertPx = Conversions.convertPx
fixDegrees = Conversions.fixDegrees

class FixedTextAnnotation:
    canvas = None
    
    def __init__(self, x=32, y=32, text=""):
        self.x = x
        self.y = y
        self.text = StringVar(value=text)
        self.id = None
        
        def updateText(*args):
            canvas = FixedTextAnnotation.canvas
            if self.id: canvas.itemconfig(self.id, text=self.text.get())
            
        self.text.trace_add("write", updateText)

    def bindGlobalVars(self, globalVars):
        canvas = FixedTextAnnotation.canvas
        
        def updatePosition(*args):
            if self.id: canvas.moveto(self.id, canvas.canvasx(self.x), canvas.canvasy(self.y))
            
        globalVars.viewOffset.trace_add("write", updatePosition)
        
    def hide(self):  
        canvas = FixedTextAnnotation.canvas
        
        if self.id: canvas.itemconfig(self.id, state="hidden")
        
    def show(self):
        canvas = FixedTextAnnotation.canvas
        if not self.id:
            self.id = canvas.create_text(canvas.canvasx(self.x), canvas.canvasy(self.y), text=self.text.get(), font=("Arial", 16), justify="left", anchor="nw", fill="red")
        else:
            canvas.itemconfig(self.id, state="normal")
        
class GeometryGrid:
    globalVars = None
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.viewOffset = GeometryGrid.globalVars.viewOffset
        
    def _convertToAbsoluteSize(self, value=0, unit="px"): 
        globalVars = GeometryGrid.globalVars
        ppi = globalVars.ppi.get()
        
        if unit == "in":
            return float(Decimal(str(value)) * Decimal(str(ppi)))
        elif unit == "cm":
            return float(Decimal(str(value)) * Decimal(str(ppi)) / Decimal("2.54"))
        elif unit == "mm":
            return float(Decimal(str(value)) * Decimal(str(ppi)) / Decimal("25.4"))
        return value
        
    def generate(self, **kwargs):
        globalVars = GeometryGrid.globalVars
        canvas = self.canvas
        
        canvas.delete(*["grid","origin"])
        if not globalVars.showGrid.get(): return
        try:
            unit = globalVars.unit.get()
            zoom = globalVars.zoom.get()/100
            size = globalVars.gridSize.get()

            #convert to pixels
            size = self._convertToAbsoluteSize(size, unit) * zoom
                
            # size = round(size)
            
            defaultKWArgs = {
                "offsetX": 0,
                "offsetY": 0,
            }
            
            defaultKWArgs.update(kwargs)
            
            canvasWidth = canvas.winfo_width()
            canvasHeight = canvas.winfo_height()
            
            offsetX = int(defaultKWArgs["offsetX"])
            offsetY = int(defaultKWArgs["offsetY"])

            # print("offset:", -offsetX, -offsetY)
            # print("scan offset:", canvas.canvasx(0), canvas.canvasy(0))
            
            totalXGridLineCount = (canvasWidth + offsetX) // size - offsetX // size
            totalYGridLineCount = (canvasHeight + offsetY) // size - offsetY // size
            
            gridLineCountThreshold = 100
            
            if totalXGridLineCount > gridLineCountThreshold or totalYGridLineCount > gridLineCountThreshold:
                size *= math.ceil(max(totalXGridLineCount, totalYGridLineCount) / 100)
            
            # # for negative coords
            for x in np.arange(-offsetX, 0, -size):
                x = canvas.canvasx(x)
                canvas.create_line(x, canvas.canvasy(canvasHeight), x, canvas.canvasy(0), tags="grid", fill="#eeeeee")
                
            for y in np.arange(-offsetY, 0, -size):
                y = canvas.canvasy(y)
                canvas.create_line(canvas.canvasx(canvasWidth), y, canvas.canvasx(0), y, tags="grid", fill="#eeeeee")
            
            # for coords x >= 0 and y >= 0
            
            for x in np.arange(-offsetX, canvasWidth, size):
                isOrigin = x == -offsetX
                x = canvas.canvasx(x)
                if isOrigin: canvas.create_line(x, canvas.canvasy(0), x, canvas.canvasy(canvasHeight), tags="origin", fill="#999999")
                else: canvas.create_line(x, canvas.canvasy(0), x, canvas.canvasy(canvasHeight), tags="grid", fill="#eeeeee")
                 
            for y in np.arange(-offsetY, canvasHeight, size):
                isOrigin = y == -offsetY
                y = canvas.canvasy(y)
                if isOrigin: canvas.create_line(canvas.canvasx(0), y, canvas.canvasx(canvasWidth), y, tags="origin", fill="#999999")
                else: canvas.create_line(canvas.canvasx(0), y, canvas.canvasx(canvasWidth), y, tags="grid", fill="#eeeeee")
                    
            canvas.tag_lower("origin")
            canvas.tag_lower("grid")
        except Exception as e:
            pass

class Point:
    canvas = None
    pointRadius = None
    viewOffset = None
    
    points = []
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.id = None
        self.StringVar = StringVar(value=self.__repr__())
        
    def __iter__(self):
        yield self.x
        yield self.y

    def __repr__(self):
        return str((self.x, self.y))
        
    def __add__(self, other):
        if isinstance(other, tuple):
            return Point(self.x + other[0], self.y + other[1])
        return Point(self.x + other.x, self.y + other.y)
        
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)
        
    def bbox(self):
        zoom = Drawing.globalVars.zoom.get()/100
        bbox = Point.canvas.bbox(self.id)

        if not self.id: return None
        return tuple(map(lambda x: round(x / zoom), bbox))
        
    def delete(self):
        if self.id != None: Drawing.canvas.delete(self.id)
        if self in Point.points: Point.points.remove(self)
        
    def magnitude(self):
        return math.hypot(self.x, self.y)
       
    def previewToOtherCanvas(self, canvas=None, **kwargs):
        defaultKWArgs = {
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        r = Point.pointRadius.get()
        
        scaleFactor = defaultKWArgs["scaleFactor"]
        
        pX = self.x
        pY = self.y
        
        canvas = Point.canvas if canvas is None else canvas
        
        canvas.create_oval((pX - r) * scaleFactor, (pY - r) * scaleFactor, (pX + r) * scaleFactor, (pY + r) * scaleFactor, tags="point", fill="blue", outline="")
        
    def setPosition(self, x, y):
        self.x = x
        self.y = y
        self.StringVar.set(repr(self))
        
    def show(self):
        r = Point.pointRadius.get()
        
        zoom = Drawing.globalVars.zoom.get()/100
        
        pX = self.x
        pY = self.y
        
        self.delete()
        
        self.id = Point.canvas.create_oval((pX - r) * zoom, (pY - r) * zoom, (pX + r) * zoom, (pY + r) * zoom, tags="point", fill="blue", outline="")
        
        if not self in Point.points: Point.points.append(self)
        
    @staticmethod
    def bboxAll():
        minX = math.inf
        minY = math.inf
        maxX = -math.inf
        maxY = -math.inf
        
        for point in Point.points:
            bbox = point.bbox()
            if not bbox: continue
            
            minX = min(minX, bbox[0])
            minY = min(minY, bbox[1])
            maxX = max(maxX, bbox[2])
            maxY = max(maxY, bbox[3])
        
        return (minX, minY, maxX, maxY)
        
    @staticmethod
    def getPointInCanvasById(pointId):
        p = [p for p in Point.points if p.id == pointId]
        if len(p) > 0: return p[0]
        return None
      
class CenterMark(Point):
    def __init__(self, x, y, size=32):
        super().__init__(x, y)
        self.size = size
        
    def previewToOtherCanvas(self, canvas=None, **kwargs):
        defaultKWArgs = {
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        size = self.size
        
        scaleFactor = defaultKWArgs["scaleFactor"]
        
        pX = self.x
        pY = self.y
        
        canvas = Point.canvas if canvas is None else canvas
        
        canvas.create_line(
            (pX - size/2) * scaleFactor, pY * scaleFactor,
            (pX + size/2) * scaleFactor, pY * scaleFactor,
            pX * scaleFactor, pY * scaleFactor,
            pX * scaleFactor, (pY - size/2) * scaleFactor,
            pX * scaleFactor, (pY + size/2) * scaleFactor,
            tags=("point", "center")
        )
        
    def show(self):
        size = self.size
        
        zoom = Drawing.globalVars.zoom.get()/100
        
        pX = self.x
        pY = self.y
        
        self.delete()
        
        self.id = Point.canvas.create_line(
            (pX - size/2) * zoom, pY * zoom,
            (pX + size/2) * zoom, pY * zoom,
            pX * zoom, pY * zoom,
            pX * zoom, (pY - size/2) * zoom,
            pX * zoom, (pY + size/2) * zoom,
            tags=("point", "center")
        )
        
        if not self in Point.points: Point.points.append(self)

class Drawing:
    drawings = []
    
    canvas = None
    globalVars = None
    pointRadius = None
    toolActivatedCounter = None
    viewOffset = None
    
    angleIncrement = None
                
    # constructor
    def __init__(self, type_="Drawing", *points, **kwargs):
        self.center = None
        self.mode = IntVar(value=0 if not "mode" in kwargs else kwargs["mode"])
        self._points = [point for point in points if point is not None]
        self.type = StringVar(value=type_)
        
        self.dashGapLength = IntVar(value=4)
        self.dashLength = IntVar(value=4)
        self.outlineColor = StringVar(value="black")
        self.outlineType = StringVar(value="solid")
        self.outlineWidth = IntVar(value=2)
        
        self.selected = BooleanVar(value=False)
        
        self.unit = Drawing.globalVars.unit
        self.topLeft = Point(0, 0)
        self.properties = Properties(
            Appearance=[
                PropertyData(self, "DashGapLength", variable=self.dashGapLength),
                PropertyData(self, "DashLength", variable=self.dashLength),
                PropertyData(self, "OutlineColor", variable=self.outlineColor),
                PropertyData(self, "OutlineType", variable=self.outlineType, options=["solid", "dash"], useOptions=True),
                PropertyData(self, "OutlineWidth", variable=self.outlineWidth),
            ],
            Data=[PropertyData(self, "Type", variable=self.type, readOnly=True)],
            Transform=[PropertyData(self, "TopLeft", variable=self.topLeft.StringVar)],
        )
        
        self.id = None
        self.initialPointOffsetPositions = None
        
        self.absoluteSizeX = DoubleVar(value=0)
        self.absoluteSizeY = DoubleVar(value=0)
        
        def selectionChanged(*args):
            canvas = Drawing.canvas
            
            if self.selected.get():
                try: canvas.itemconfig(self.id, outline="blue")
                except: canvas.itemconfig(self.id, fill="blue")
            else:
                try: canvas.itemconfig(self.id, outline=self.outlineColor.get())
                except: canvas.itemconfig(self.id, fill=self.outlineColor.get())
            
        self.selected.trace_add("write", selectionChanged)
        
        def propertyChanged(prop, value=""):
            name = prop.name
            lastValue = prop.lastValue
            
            if name == "TopLeft":
                matchA = re.search(r"^([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)$", value.strip()) # without parentheses
                matchB = re.search(r"^\(\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\)$", value.strip()) # with parentheses
                
                match = None
                
                if matchA: match = matchA
                elif matchB: match = matchB  
                
                if match:
                    x = float(match.group(1))
                    y = float(match.group(2))
                    
                    self.moveTo(x, y)
            elif name == "OutlineColor" or name == "OutlineType" or name == "OutlineWidth" or name == "DashGapLength" or name == "DashLength":
                self.redraw()
        
        self.properties.onChange.append(propertyChanged)
        
    def addPoint(self, point):
        self._points.append(point)
        
    def absoluteSize(self):
        minX = min([point.x for point in self._points])
        minY = min([point.y for point in self._points])
        maxX = max([point.x for point in self._points])
        maxY = max([point.y for point in self._points])
        
        return (maxX - minX, maxY - minY)
    
    def baseCnf(self):
        cnf = {
            "tags": "drawing",
            "width": self.outlineWidth.get(),
        }
        
        if self.outlineType.get() == "dash": cnf["dash"] = (self.dashLength.get(), self.dashGapLength.get())
        
        return cnf
        
    def bbox(self):
        zoom = Drawing.globalVars.zoom.get()/100

        if not self.id: return None
        return tuple(map(lambda x: x / zoom, Drawing.canvas.bbox(self.id)))
        
    def delete(self):
        if self.id != None: Drawing.canvas.delete(self.id)
        if self in Drawing.drawings: Drawing.drawings.remove(self)
        for p in self._points: p.delete()
        
    def draw(self): # main draw method
        self.redraw()
        
        d = DrawCommand(drawing=self)
        Drawing.globalVars.historyManager.do(d)
        
    def getPoints(self):
        return self._points
        
    def motion(self, event):
        tool = Drawing.globalVars.tool.get()
        
        if tool == "Dimension":
            try:
                Drawing.canvas.itemconfig(self.id, outline="blue")
            except:
                Drawing.canvas.itemconfig(self.id, fill="blue")
        
    def mouseLeave(self, event):
        tool = Drawing.globalVars.tool.get()
        
        if tool == "Dimension":
            try:
                Drawing.canvas.itemconfig(self.id, outline="black")
            except:
                Drawing.canvas.itemconfig(self.id, fill="black")
        
    def moveTo(self, x, y):
        pointOffsetPositions = self.initialPointOffsetPositions
        
        zoom = Drawing.globalVars.zoom.get()/100
        
        Drawing.canvas.moveto(self.id, x * zoom, y * zoom)
        
        for point in self._points:
            point.x = x + pointOffsetPositions[point].x
            point.y = y + pointOffsetPositions[point].y
        
        self.showPoints()
        
    def pointOffsetPositions(self): # offset relative to top left of drawing
        bbox = self.bbox()
        pointOffsetPositions = {}
        
        if not bbox: return pointOffsetPositions
        
        x = bbox[0]
        y = bbox[1]
        
        for point in self._points:
            pointOffsetPositions[point] = Point(point.x - x, point.y - y)
            
        return pointOffsetPositions
        
    def predict(self, nextPoint):
        self._onPredict(nextPoint)
        
    def previewToOtherCanvas(self, canvas=None):
        canvas = Drawing.canvas if canvas is None else canvas
        
        self._onDraw(canvas, assignId=False, scaleFactor=1)
        
        self.previewPointsToOtherCanvas(canvas)
    
    def redraw(self):
        canvas = Drawing.canvas
        if self.id: Drawing.canvas.delete(self.id)
        
        if not self in Drawing.drawings: Drawing.drawings.append(self)
        
        self._onDraw()
        
        scaleFactor = Drawing.globalVars.zoom.get()/100
        
        if self.id: 
            Drawing.canvas.tag_bind(self.id, "<Motion>", self.motion)
            Drawing.canvas.tag_bind(self.id, "<Leave>", self.mouseLeave)
            
            Drawing.canvas.scale(self.id, 0, 0, scaleFactor, scaleFactor)
        
        for point in self._points:
            if point.id: Drawing.canvas.scale(point.id, 0, 0, scaleFactor, scaleFactor)
            
        bbox = Drawing.canvas.bbox(self.id)
        
        self.topLeft.setPosition(bbox[0] / scaleFactor, bbox[1] / scaleFactor)
        
        self.absoluteSizeX.set(bbox[2] - bbox[0])
        self.absoluteSizeY.set(bbox[3] - bbox[1])
            
        self.initialPointOffsetPositions = self.pointOffsetPositions()
        
        self.showPoints()
        
        canvas.tag_lower("point")
        canvas.tag_lower("drawing")
        canvas.tag_lower("dimension")
        canvas.tag_lower("origin")
        canvas.tag_lower("grid")
            
    def setCenter(self, center):
        self.center = center
        if not self.center in self._points: self.addPoint(self.center)
        
    def showPoints(self):
        for point in self._points: 
            point.delete()
            if Drawing.globalVars.showOtherPoints.get(): point.show()
            
        if hasattr(self, "center"):
            if self.center: 
                self.center.delete()
                if Drawing.globalVars.showCenter.get(): self.center.show()
                
    def previewPointsToOtherCanvas(self, canvas=None):
        for point in self._points: 
            point.previewToOtherCanvas(canvas)
            
        if hasattr(self, "center"):
            if self.center: 
                if Drawing.globalVars.showCenter.get(): self.center.previewToOtherCanvas(canvas)

    @staticmethod
    def bboxAll():
        minX = math.inf
        minY = math.inf
        maxX = -math.inf
        maxY = -math.inf
        
        for drawing in Drawing.drawings:
            bbox = drawing.bbox()
            if not bbox: continue
            
            minX = min(minX, bbox[0])
            minY = min(minY, bbox[1])
            maxX = max(maxX, bbox[2])
            maxY = max(maxY, bbox[3])
        
        return (minX, minY, maxX, maxY)
        
    @staticmethod
    def getAllPoints():
        points = []
        for i in Drawing.drawings:
            for j in i.getPoints():
                points.append(j)
        return points
        
    @staticmethod
    def getDrawingById(drawingId):
        for drawing in Drawing.drawings:
            if drawing.id == drawingId: return drawing
        return None
        
    @staticmethod
    def redrawAll():
        for drawing in Drawing.drawings: drawing.redraw()
        
    @staticmethod
    def showAllPoints():
        for drawing in Drawing.drawings:
            drawing.showPoints()
        
class Circle(Drawing):
    def __init__(self, *points, **kwargs):
        super().__init__("Circle", *points, **kwargs)
        self.absoluteRadius = DoubleVar(value=0)
        self.radius = DoubleVar(value=0)

        self.properties.update(
            Dimensions=[PropertyData(self, "Radius", variable=self.radius, useUnit=True)]
        )
        
        def propertyChanged(prop, value=""):
            name = prop.name
            lastValue = prop.lastValue
            
            p = self._points
            toolMode = self.mode.get()
            
            if name == "Radius":
                self.absoluteRadius.set(convertToAbsoluteSize(self.radius.get(), self.unit.get()))
                
                r = self.absoluteRadius.get()
                
                if toolMode == 1:
                    centerX = self.center.x
                    centerY = self.center.y
                    
                    angle1 = math.atan2(centerY - p[0].y, p[0].x - centerX)
                    angle2 = math.atan2(centerY - p[1].y, p[1].x - centerX)
                    
                    p[0].setPosition(
                        centerX + r * math.cos(angle1),
                        centerY - r * math.sin(angle1)
                    )
                    
                    p[1].setPosition(
                        centerX + r * math.cos(angle2),
                        centerY - r * math.sin(angle2)
                    )
                
                self.redraw()
        
        self.properties.onChange.append(propertyChanged)
        
        Drawing.globalVars.unit.trace_add("write", lambda *args: self.radius.set(convertPx(self.absoluteRadius.get(), self.unit.get())))
    
    def absoluteSize(self):
        minX = self.center.x - self.absoluteRadius.get()
        minY = self.center.y - self.absoluteRadius.get()
        maxX = self.center.x + self.absoluteRadius.get()
        maxY = self.center.y + self.absoluteRadius.get()
        
        return (maxX - minX, maxY - minY)
        
    def _onDraw(self, canvas=None, **kwargs):  
        defaultKWArgs = {
            "assignId": True,
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        canvas = Drawing.canvas if canvas is None else canvas
        p = self._points
        n = len(p)
        
        r = self.absoluteRadius.get()
        toolMode = self.mode.get()
        
        canvas.delete("prediction")
        
        if toolMode == 1:
            x0 = p[0].x
            y0 = p[0].y
            x1 = p[1].x
            y1 = p[1].y
            
            self.setCenter(CenterMark((x0 + x1) / 2, (y0 + y1) / 2))
                
        minX, minY, maxX, maxY = (
            self.center.x - r,
            self.center.y - r,
            self.center.x + r,
            self.center.y + r
        )
        
        scaleFactor = defaultKWArgs["scaleFactor"]
        
        minX *= scaleFactor
        minY *= scaleFactor
        maxX *= scaleFactor
        maxY *= scaleFactor
        
        cnf = self.baseCnf()
        
        if defaultKWArgs["assignId"]: 
            self.id = canvas.create_oval(minX, minY, maxX, maxY, cnf)
        else:
            canvas.create_oval(minX, minY, maxX, maxY, cnf)
        
    def _onPredict(self, nextPoint):
        globalVars = Drawing.globalVars
        
        vX = Drawing.viewOffset.x.get()
        vY = Drawing.viewOffset.y.get()
        
        zoom = globalVars.zoom.get()/100
        
        p = self._points
        n = len(p)
        
        Drawing.canvas.delete("prediction")
        
        toolMode = self.mode.get()
        
        if toolMode == 0:
            if Drawing.toolActivatedCounter.get() == 1:
                x0 = self.center.x
                y0 = self.center.y
                x1 = nextPoint.x
                y1 = nextPoint.y
                
                self.absoluteRadius.set(math.hypot(x1 - x0, y1 - y0))
                self.radius.set(convertPx(self.absoluteRadius.get(), self.unit.get()))
                
                x0 *= zoom
                y0 *= zoom
                x1 *= zoom
                y1 *= zoom
                
                magnitude = self.absoluteRadius.get() * zoom
                
                Drawing.canvas.create_line(x0, y0, x1, y1, tags="prediction", fill="blue", dash=(16, 16), width=1, arrow=BOTH, arrowshape=globalVars.dimensionArrowShape)
                Drawing.canvas.create_oval(x0 - magnitude, y0 - magnitude, x0 + magnitude, y0 + magnitude, tags="prediction", outline="blue")
        elif toolMode == 1:
            if Drawing.toolActivatedCounter.get() == 1:
                x0 = p[0].x
                y0 = p[0].y
                x1 = nextPoint.x
                y1 = nextPoint.y
                
                # self.absoluteRadius.set(math.hypot(x1 - x0, y1 - y0))
                # self.radius.set(convertPx(self.absoluteRadius.get(), self.unit.get()))
                
                self.absoluteRadius.set(math.hypot(x1 - x0, y1 - y0) / 2)
                self.radius.set(convertPx(self.absoluteRadius.get(), self.unit.get()))
                
                x0 *= zoom
                y0 *= zoom
                x1 *= zoom
                y1 *= zoom
                
                midpointX = (x0 + x1) / 2
                midpointY = (y0 + y1) / 2

                magnitude = self.absoluteRadius.get() * zoom
                
                Drawing.canvas.create_line(x0, y0, x1, y1, tags="prediction", fill="blue", dash=(4,4))
                Drawing.canvas.create_oval(midpointX - magnitude, midpointY - magnitude, midpointX + magnitude, midpointY + magnitude, tags="prediction", outline="blue")

class TextDrawing(Drawing):
    def _update(self, canvas=None, **kwargs):   
        canvas = Drawing.canvas if canvas is None else canvas
        
        self.kwargs.update(**kwargs)
        
        if self.id is None: return
        canvas.itemconfig(self.id, text=self.text.get(), justify=self.justify.get(), **self.kwargs)
        
    def __init__(self, point, **kwargs):
        super().__init__("Text", point, **kwargs)
        self.justify = StringVar(value="left")
        self.text = StringVar(value="")
        self._insertionPoint = False
        self.fontFamily = StringVar(value="Arial")
        self.fontSize = IntVar(value=14)
        
        self.kwargs = {
            "anchor": "nw"
        }
        
        self.properties.update(
            Text=[
                PropertyData(self, "Justify", variable=self.justify, options=["left", "center", "right"], useOptions=True),
                PropertyData(self, "Text", variable=self.text)
            ]
        )
        
        self._update(**kwargs)
        
        def propertyChanged(prop, value=""):
            self.redraw()
            self._update()
        
        def textUpdate(*args):
            self._update()
            
        self.properties.onChange.append(propertyChanged)
        
        self.text.trace_add("write", textUpdate)

    def _onDraw(self, canvas=None, **kwargs):   
        defaultKWArgs = {
            "assignId": True,
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        canvas = Drawing.canvas if canvas is None else canvas
        
        p = self._points
        
        scaleFactor = defaultKWArgs["scaleFactor"]
        
        if len(p) <= 0: return
        
        x = p[0].x 
        y = p[0].y
        
        if defaultKWArgs["assignId"]:
            self.id = canvas.create_text(x, y, tags="drawing", justify=self.justify.get(), font=(self.fontFamily.get(), self.fontSize.get() * scaleFactor), **self.kwargs)
            self._update(canvas)
        else:
            canvas.create_text(x, y, tags="drawing", text=self.text.get(), justify=self.justify.get(), font=(self.fontFamily.get(), self.fontSize.get() * scaleFactor), **self.kwargs)
        
    def _keyPress(self, event):
        keysym = event.keysym
        char = event.char
        
        self.text.set(self.text.get() + char)
            
        self._insertionPoint = True
        self.blink()
            
    def _backspace(self, event):
        self.text.set(self.text.get()[:-1])
        
        self._insertionPoint = True
        self.blink()
        
    def _copy(self, event):
        print("copy")
        
    def _paste(self, event):
        self.text.set(self.text.get() + Drawing.globalVars.root.clipboard_get())
        
    def blink(self):
        Drawing.canvas.itemconfig(self.id, text=self.text.get() + "|")
        
    def unblink(self):
        Drawing.canvas.itemconfig(self.id, text=self.text.get())
        
    def startBlinkLoop(self):
        if self._edit:
            self._insertionPoint = not self._insertionPoint

            if self.id:
                if self._insertionPoint: self.blink()
                else: self.unblink()
            Drawing.globalVars.root.after(500, self.startBlinkLoop)
            
    def stopBlinkLoop(self):
        self.unblink()
        self._insertionPoint = False
        
    def startEdit(self):
        self._edit = True
        self.keyPress = Drawing.globalVars.root.bind("<Key>", self._keyPress, add="+")
        self.copy = Drawing.globalVars.root.bind("<Control-c>", self._copy, add="+")
        self.paste = Drawing.globalVars.root.bind("<Control-v>", self._paste, add="+")
        self.backspace = Drawing.globalVars.root.bind("<BackSpace>", self._backspace, add="+")
        
        self._insertionPoint = False
        self.startBlinkLoop()
        
    def finishEdit(self):
        self._edit = False
        Drawing.globalVars.root.unbind("<Key>", self.keyPress)
        Drawing.globalVars.root.unbind("<Control-c>", self.copy)
        Drawing.globalVars.root.unbind("<Control-v>", self.paste)
        Drawing.globalVars.root.unbind("<BackSpace>", self.backspace)
        
        if self.text.get().strip() == "":
            self.delete()
        
        self.stopBlinkLoop()
        
class Line(Drawing):
    def __init__(self, *points, **kwargs):
        super().__init__("Line", *points, **kwargs)
        self.absoluteLength = DoubleVar(value=0)
        self.length = DoubleVar(value=0)
        
        Drawing.globalVars.unit.trace_add("write", lambda a, b, c: self.length.set(convertPx(self.absoluteLength.get(), self.unit.get())))
        
    def _onDraw(self, canvas=None, **kwargs):   
        defaultKWArgs = {
            "assignId": True,
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        canvas = Drawing.canvas if canvas is None else canvas
        
        p = self._points
        n = len(p)
        
        canvas.delete("prediction")
        
        scaleFactor = defaultKWArgs["scaleFactor"]
        
        x1 = p[0].x * scaleFactor
        y1 = p[0].y * scaleFactor
        x2 = p[1].x * scaleFactor
        y2 = p[1].y * scaleFactor
        
        cnf = self.baseCnf()
   
        if defaultKWArgs["assignId"]:
            self.id = canvas.create_line(x1, y1, x2, y2, cnf)
        else:
            canvas.create_line(x1, y1, x2, y2, cnf)
        
    def _onPredict(self, nextPoint):
        globalVars = Drawing.globalVars
        
        p = self._points
        n = len(p)
        
        zoom = globalVars.zoom.get()/100
        
        Drawing.canvas.delete("prediction")
        
        if Drawing.toolActivatedCounter.get() == 1:
            x1 = p[0].x
            y1 = p[0].y
            x2 = nextPoint.x
            y2 = nextPoint.y
            
            absoluteLength = (p[0] - nextPoint).magnitude()
            length = convertPx(absoluteLength, self.unit.get())
            
            self.absoluteLength.set(absoluteLength)
            self.length.set(length)
            
            Drawing.canvas.create_line(x1 * zoom, y1 * zoom, x2 * zoom, y2 * zoom, tags="prediction", fill="blue", dash=(16, 16), width=1, arrow=BOTH, arrowshape=globalVars.dimensionArrowShape)

class Rectangle(Drawing):
    def __init__(self, *points, **kwargs):
        super().__init__("Rectangle", *points, **kwargs)
        
        self.length = DoubleVar(value=0)
        self.width = DoubleVar(value=0)
        
        self.absoluteLength = DoubleVar(value=0)
        self.absoluteWidth = DoubleVar(value=0)
        
        self.startEndDiff = Point(0, 0)
        
        self.properties.update(
            Dimensions=[
                PropertyData(self, "Length", variable=self.length, useUnit=True),
                PropertyData(self, "Width", variable=self.width, useUnit=True),
            ],
        )
        
        def propertyChanged(prop, value=""):
            name = prop.name
            
            if name == "Length":
                self.absoluteLength.set(convertToAbsoluteSize(self.length.get(), self.unit.get()))
                self.redraw()
            elif name == "Width":
                self.absoluteWidth.set(convertToAbsoluteSize(self.width.get(), self.unit.get()))
                self.redraw()
                
        self.properties.onChange.append(propertyChanged)
        
        def unitChanged(*args):
            self.length.set(convertPx(self.absoluteLength.get(), self.unit.get()))
            self.width.set(convertPx(self.absoluteWidth.get(), self.unit.get()))
            
        Drawing.globalVars.unit.trace_add("write", unitChanged)
        
    def _onDraw(self, canvas=None, **kwargs):   
        defaultKWArgs = {
            "assignId": True,
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        canvas = Drawing.canvas if canvas is None else canvas
        
        p = self._points
        n = len(p)
        
        Drawing.canvas.delete("prediction")
        
        scaleFactor = defaultKWArgs["scaleFactor"]

        startPoint = p[0]
        endPoint = p[2]
        
        startEndDiffX = endPoint.x - startPoint.x
        startEndDiffY = endPoint.y - startPoint.y
        
        diffXSign = float(np.sign(startEndDiffX))
        diffYSign = float(np.sign(startEndDiffY))
        
        length = self.absoluteLength.get()
        width = self.absoluteWidth.get()
        
        p[1].setPosition(startPoint.x + length * diffXSign, startPoint.y)
        endPoint.setPosition(startPoint.x + length * diffXSign, startPoint.y + width * diffYSign)
        p[3].setPosition(startPoint.x, startPoint.y + width * diffYSign)
        
        startEndDiffX = endPoint.x - startPoint.x
        startEndDiffY = endPoint.y - startPoint.y
        
        self.startEndDiff.setPosition(startEndDiffX, startEndDiffY)
        
        x1 = startPoint.x * scaleFactor
        y1 = startPoint.y * scaleFactor
        x2 = endPoint.x * scaleFactor
        y2 = endPoint.y * scaleFactor
        
        cnf = self.baseCnf()
        
        if defaultKWArgs["assignId"]:
            self.id = canvas.create_rectangle(x1, y1, x2, y2, cnf)
        else: 
            canvas.create_rectangle(x1, y1, x2, y2, cnf)
        
    def _onPredict(self, nextPoint):
        p = self._points
        n = len(p)
        
        zoom = Drawing.globalVars.zoom.get()/100
        
        Drawing.canvas.delete("prediction")
        
        if Drawing.toolActivatedCounter.get() == 1:
            x1 = p[0].x
            y1 = p[0].y
            x2 = nextPoint.x
            y2 = nextPoint.y
            
            self.startEndDiff.setPosition(x2 - x1, y2 - y1)
            
            self.absoluteLength.set(abs(self.startEndDiff.x))
            self.absoluteWidth.set(abs(self.startEndDiff.y))
            
            self.length.set(convertPx(self.absoluteLength.get(), self.unit.get()))
            self.width.set(convertPx(self.absoluteWidth.get(), self.unit.get()))
            
            Drawing.canvas.create_rectangle(x1 * zoom, y1 * zoom, x2 * zoom, y2 * zoom, tags="prediction", outline="blue")

class Arc(Drawing):
    def __init__(self, *points, **kwargs):
        super().__init__("Arc", *points, **kwargs)
        self.start = DoubleVar(value=0)
        self.end = DoubleVar(value=0)
        
        self.startPoint = Point(0, 0)
        self.endPoint = Point(0, 0)
        
        self.addPoint(self.startPoint)
        self.addPoint(self.endPoint)
        
        self.absoluteRadius = DoubleVar(value=0)
        self.radius = DoubleVar(value=0)
        
        self.properties.update(
            Dimensions=[
                PropertyData(self, "AngleBegin", variable=self.start),
                PropertyData(self, "AngleEnd", variable=self.end),
                PropertyData(self, "Radius", variable=self.radius, useUnit=True)
            ],
        )
        
        def propertyChanged(prop, value=""):
            name = prop.name
            lastValue = prop.lastValue
            
            pR = Drawing.pointRadius.get()
            
            if name == "Radius": self.absoluteRadius.set(convertToAbsoluteSize(self.radius.get(), self.unit.get()))
                
            r = self.absoluteRadius.get()
            
            self.startPoint.setPosition(
                self.center.x + r * math.cos(math.radians(self.start.get())),
                self.center.y - r * math.sin(math.radians(self.start.get()))
            )
            
            self.endPoint.setPosition(
                self.center.x + r * math.cos(math.radians(self.end.get())),
                self.center.y - r * math.sin(math.radians(self.end.get()))
            )

            self.redraw()
        
        self.properties.onChange.append(propertyChanged)
        
        Drawing.globalVars.unit.trace_add("write", lambda a, b, c: self.radius.set(convertPx(self.absoluteRadius.get(), self.unit.get())))
        
    def _onDraw(self, canvas=None, **kwargs):   
        defaultKWArgs = {
            "assignId": True,
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        canvas = Drawing.canvas if canvas is None else canvas
        
        p = self._points
        n = len(p)
        
        zoom = Drawing.globalVars.zoom.get()/100
        
        r = self.absoluteRadius.get()
        
        Drawing.canvas.delete("prediction")
        
        minX, minY, maxX, maxY = (
            self.center.x - r,
            self.center.y - r,
            self.center.x + r,
            self.center.y + r
        )
        
        scaleFactor = defaultKWArgs["scaleFactor"]
        
        minX *= scaleFactor
        minY *= scaleFactor
        maxX *= scaleFactor
        maxY *= scaleFactor
        
        self.extent = fixDegrees(self.end.get() - self.start.get())
        
        cnf = self.baseCnf()
        
        if defaultKWArgs["assignId"]:
            self.id = canvas.create_arc(minX, minY, maxX, maxY, cnf, start=self.start.get(), extent=self.extent, style="arc")
        else:
            canvas.create_arc(minX, minY, maxX, maxY, cnf, start=self.start.get(), extent=self.extent, style="arc")
            
    def _onPredict(self, nextPoint):
        globalVars = Drawing.globalVars
        
        vX = Drawing.viewOffset.x.get()
        vY = Drawing.viewOffset.y.get()
        
        zoom = globalVars.zoom.get()/100
        
        p = self._points
        n = len(p)
        
        pR = Drawing.pointRadius.get()
        r = self.absoluteRadius.get()
        
        Drawing.canvas.delete("prediction")
        
        if Drawing.toolActivatedCounter.get() == 1:
            x0 = self.center.x
            y0 = self.center.y
            x1 = nextPoint.x
            y1 = nextPoint.y
            
            self.absoluteRadius.set(math.sqrt((x1 - x0)**2 + (y1 - y0)**2))
            self.radius.set(convertPx(self.absoluteRadius.get(), self.unit.get()))
            
            x0 *= zoom
            y0 *= zoom
            x1 *= zoom
            y1 *= zoom
                
            Drawing.canvas.create_line(x0, y0, x1, y1, tags="prediction", fill="blue", dash=(16, 16), width=1, arrow=BOTH, arrowshape=globalVars.dimensionArrowShape)
        elif Drawing.toolActivatedCounter.get() == 2:
            def drawArcArrow(canvas, x0, y0, x1, y1, startDeg, extentDeg, **kwargs):
                lineKWArgs = dict(kwargs)
                
                if "outline" in lineKWArgs:
                    lineKWArgs["fill"] = kwargs["outline"]
                    del lineKWArgs["outline"]
                
                canvas.create_arc(x0, y0, x1, y1, start=startDeg, extent=extentDeg, style="arc", **kwargs)
                
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
                
                endRad = math.radians(startDeg + extentDeg)
                endX = cx + rx * math.cos(endRad)
                endY = cy - ry * math.sin(endRad)
                
                stepDeg = -1 if extentDeg > 0 else 1
                prevRad = math.radians(startDeg + extentDeg + stepDeg)
                prevX = cx + rx * math.cos(prevRad)
                prevY = cy - ry * math.sin(prevRad)
                
                canvas.create_line(prevX, prevY, endX, endY, arrow=LAST, arrowshape=globalVars.dimensionArrowShape, **lineKWArgs)
                
            previewArcPos = (
                self.center.x - r,
                self.center.y - r,
                self.center.x + r,
                self.center.y + r
            )
            
            angleDisplayScale = 1/3
            
            angleDisplayPos = (
                self.center.x - r * angleDisplayScale,
                self.center.y - r * angleDisplayScale,
                self.center.x + r * angleDisplayScale,
                self.center.y + r * angleDisplayScale
            )
            
            previewArcPos = tuple(map(lambda coord: coord * zoom, previewArcPos))
            angleDisplayPos = tuple(map(lambda coord: coord * zoom, angleDisplayPos))
            
            x0 = self.center.x
            y0 = self.center.y
            
            x1 = p[0].x
            y1 = p[0].y
            
            x2 = nextPoint.x
            y2 = nextPoint.y
            
            startDiffX = x1 - self.center.x
            endDiffX = x2 - self.center.x
            
            startDiffY = self.center.y - y1
            endDiffY = self.center.y - y2
            
            startAngle = fixDegrees(math.degrees(math.atan2(startDiffY, startDiffX)))
            endAngle = fixDegrees(math.degrees(math.atan2(endDiffY, endDiffX)))
            
            angleIncrement = Drawing.angleIncrement.get()

            if Drawing.globalVars.snapToRotate.get(): endAngle = angleIncrement * round(endAngle / angleIncrement) + startAngle % angleIncrement
            
            endAngle = fixDegrees(endAngle)
            
            self.start.set(startAngle)  
            self.end.set(endAngle)
                
            self.extent = fixDegrees(self.end.get() - self.start.get())
                
            pX = self.center.x + r * math.cos(math.radians(self.end.get())) - pR
            pY = self.center.y - r * math.sin(math.radians(self.end.get())) - pR
            
            textAngle = (2 * self.start.get() + self.extent) / 2
            
            textPosX = self.center.x + r * angleDisplayScale * math.cos(math.radians(textAngle))
            textPosY = self.center.y - r * angleDisplayScale * math.sin(math.radians(textAngle))
            
            pX *= zoom
            pY *= zoom
            
            x0 *= zoom
            y0 *= zoom
            
            x1 *= zoom
            y1 *= zoom
            
            x2 *= zoom
            y2 *= zoom
            
            textPosX *= zoom
            textPosY *= zoom
                
            Drawing.canvas.create_line(x0, y0, x1, y1, tags="prediction", fill="blue", dash=(16, 16), width=1, arrow=LAST, arrowshape=globalVars.dimensionArrowShape) # start line
            Drawing.canvas.create_line(x0, y0, pX, pY, tags="prediction", fill="blue", dash=(16, 16), width=1) # end line
            
            Drawing.canvas.create_arc(*previewArcPos, start=startAngle, extent=self.extent, tags="prediction", outline="blue", style="arc") # main arc
            drawArcArrow(Drawing.canvas, *angleDisplayPos, startAngle, self.extent, tags="prediction", outline="blue") # for angle display
            
            Drawing.canvas.create_text(
                textPosX, 
                textPosY, 
                text=self.extent, 
                tags="prediction", fill="blue", 
                font=("Arial", 14),
                angle=textAngle - 90,
                anchor="s"
            )
            
            Drawing.canvas.moveto("pointPosition", pX, pY)
        
class Dimension:
    dimensions = []
    
    canvas = None
    globalVars = None
    
    def __init__(self, type_="Dimension", **kwargs):
        canvas = Dimension.canvas
        globalVars = Dimension.globalVars
        
        self.type = StringVar(value=type_)
        self.absoluteSize = DoubleVar(value=0)
        self.annotationIds = []
        self.drawing = None # drawing to reference
        self.id = None
        self._points = []
        self.referencePoint = None # point to reference
        
        self.color = StringVar(value="red")
        self.customLabel = StringVar(value="")
        self.outlineWidth = IntVar(value=2)
        self.useCustomLabel = BooleanVar(value=False)
        self.unit = StringVar(value=globalVars.unit.get())
        
        self.properties = Properties(
            Appearance=[
                PropertyData(self, "Color", variable=self.color),
                PropertyData(self, "CustomLabel", variable=self.customLabel),
                PropertyData(self, "OutlineWidth", variable=self.outlineWidth),
                PropertyData(self, "UseCustomLabel", variable=self.useCustomLabel, makePropertiesReadOnlyIf={False: ["CustomLabel"]}),
            ],
            Data=[
                PropertyData(self, "AbsoluteSize", variable=self.absoluteSize, readOnly=True),
                PropertyData(self, "Type", variable=self.type, readOnly=True),
            ],
        )
        
        def propertyChanged(prop, value=""):
            name = prop.name
            lastValue = prop.lastValue
            
            if name == "Color" or name == "OutlineWidth" or name == "UseCustomLabel" or name == "CustomLabel":
                self.redraw()
        
        self.properties.onChange.append(propertyChanged)
        
        globalVars.unit.trace_add("write", self._unitChanged)
        
    def addPoint(self, point):
        self._points.append(point)
        
    def bbox(self):
        canvas = Dimension.canvas
        zoom = Dimension.globalVars.zoom.get()/100
        
        minX = math.inf
        minY = math.inf
        maxX = -math.inf
        maxY = -math.inf
        
        if len(self.annotationIds) > 0:
            for annotationId in self.annotationIds:
                bbox = canvas.bbox(annotationId)
                
                if bbox:
                    x1, y1, x2, y2 = bbox
                    
                    minX = min(minX, x1)
                    minY = min(minY, y1)
                    maxX = max(maxX, x2)
                    maxY = max(maxY, y2)
            
            return (minX / zoom, minY / zoom, maxX / zoom, maxY / zoom)
        else:
            return (0, 0, 0, 0)
        
    def delete(self):
        canvas = Dimension.canvas
        for anotationId in self.annotationIds:
            canvas.delete(anotationId)
        if self in Dimension.dimensions: Dimension.dimensions.remove(self)
        
    def draw(self):
        self.redraw()
        
        dimensionSelectionType = Dimension.globalVars.dimensionSelectionType.get()
        
        d = DimensionCommand(dimension=self, mode=Dimension.globalVars.toolObject.mode.get(), dimensionSelectionType=dimensionSelectionType)
        Dimension.globalVars.historyManager.do(d)
        
    def predict(self, nextPoint):
        self._onPredict(nextPoint)
       
    def previewToOtherCanvas(self, canvas=None):   
        canvas = Dimension.canvas if canvas is None else canvas
        
        self._onDraw(canvas, assignId=False) 
        
    def redraw(self):
        self.delete()
        
        canvas = Dimension.canvas
        globalVars = Dimension.globalVars
        
        zoom = globalVars.zoom.get() / 100
        
        self._onDraw(scaleFactor=zoom)
        
        canvas.tag_lower("point")
        canvas.tag_lower("drawing")
        canvas.tag_lower("dimension")
        canvas.tag_lower("origin")
        canvas.tag_lower("grid")
        
        if not self in Dimension.dimensions: Dimension.dimensions.append(self)

    def _unitChanged(self, a, b, c):
        canvas = Dimension.canvas
        text = [i for i in self.annotationIds if canvas.type(i) == "text"]
        if len(text) <= 0: return
        text = text[0]
        
        canvas.itemconfig(text, text=f"{round(Dimension._convertPx(self.absoluteSize.get(), Dimension.globalVars.unit.get()), 4)}")
        
    @staticmethod
    def bboxAll():
        minX = math.inf
        minY = math.inf
        maxX = -math.inf
        maxY = -math.inf
        
        for dimension in Dimension.dimensions:
            bbox = dimension.bbox()
            if not bbox: continue
            
            minX = min(minX, bbox[0])
            minY = min(minY, bbox[1])
            maxX = max(maxX, bbox[2])
            maxY = max(maxY, bbox[3])
        
        return (minX, minY, maxX, maxY)
        
    def _convertPx(value=0, unit="px"):
        globalVars = Dimension.globalVars
        ppi = globalVars.ppi.get()
        
        if unit == "in":
            return float(Decimal(str(value)) / Decimal(str(ppi)))
        elif unit == "cm":
            return float(Decimal(str(value)) / (Decimal(str(ppi)) / Decimal("2.54")))
        elif unit == "mm":
            return float(Decimal(str(value)) / (Decimal(str(ppi)) / Decimal("25.4")))
        return value
        
    @staticmethod
    def getDimensionByAnnotationId(annotationId):
        for dimension in Dimension.dimensions:
            if annotationId in dimension.annotationIds: return dimension
        return None 
    
    @staticmethod  
    def redrawAll():
        for dimension in Dimension.dimensions: 
            dimension.delete()
            dimension.redraw()
        
class LinearDimension(Dimension):
    def __init__(self, **kwargs):
        super().__init__("Linear", **kwargs)
        
    def createAnnotation(self, position, canvas=None, **kwargs):   
        defaultKWArgs = {
            "assignId": True,
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        kwargs = defaultKWArgs
        
        canvas = Dimension.canvas if canvas is None else canvas
        
        globalVars = Dimension.globalVars
        arrowShape = globalVars.dimensionArrowShape

        tags = kwargs["tags"] if "tags" in kwargs else ""
        fill = kwargs["fill"] if "fill" in kwargs else "black"
        scaleFactor = kwargs["scaleFactor"]
        
        dimensionSelectionType = Dimension.globalVars.dimensionSelectionType.get()
        unit = Dimension.globalVars.unit.get()
        
        x1 = None
        y1 = None
        x2 = None
        y2 = None
        absoluteSizeX = 0
        absoluteSizeY = 0
        absoluteSize = 0
        
        textPosX = 0
        textPosY = 0
        
        line1 = None
        line2 = None
        arrow1 = None
        arrow2 = None
        text = None
        
        line1StartX = line1StartY = line1EndY = line2StartX = line2StartY = line2EndY = line1EndX = line2EndX = None
        arrow1StartX = arrow1StartY = arrow1EndY = arrow2StartX = arrow2StartY = arrow2EndY = arrow1EndX = arrow2EndX = None
        
        drawingType = ""
        dimensionLabel = ""
        
        if dimensionSelectionType == "Drawing":
            if self.drawing:
                drawingType = self.drawing.type.get()
                match drawingType:
                    case "Circle":
                        _p = self.drawing.getPoints()
                        x1 = self.drawing.center.x - self.drawing.absoluteRadius.get()
                        y1 = self.drawing.center.y - self.drawing.absoluteRadius.get()
                        x2 = self.drawing.center.x + self.drawing.absoluteRadius.get()
                        y2 = self.drawing.center.y + self.drawing.absoluteRadius.get()
                    case _:
                        _p = self.drawing.getPoints()
                        x1 = _p[0].x
                        x2 = _p[1].x
                        y1 = _p[0].y
                        y2 = _p[1].y

                absoluteSizeX, absoluteSizeY = self.drawing.absoluteSize()
        elif dimensionSelectionType == "Point":
            if len(self._points) >= 2:
                x1 = self._points[0].x
                y1 = self._points[0].y
                x2 = self._points[1].x
                y2 = self._points[1].y
                
                absoluteSizeX = abs(x2 - x1)
                absoluteSizeY = abs(y2 - y1)
                
        midpointX = (x1 + x2) / 2
        midpointY = (y1 + y2) / 2
        
        diffX = position.x - midpointX
        diffY = position.y - midpointY
        
        angle = 0
        
        customFont = font.Font(
            family=globalVars.dimensionTextFontFamily.get(), 
            size=int(globalVars.dimensionTextFontSize.get() * scaleFactor), 
            weight=globalVars.dimensionTextFontWeight.get(), 
            slant=globalVars.dimensionTextSlant.get()
        )
        
        arrowWidth = arrowShape[2]

        if self.drawing:
            match drawingType:
                case "Circle": 
                    if abs(diffX) > abs(diffY): x1 = x2 = self.drawing.center.x # sideward
                    elif abs(diffX) < abs(diffY): y1 = y2 = self.drawing.center.y # upward / downward
                    
                case "Rectangle":
                    if abs(diffX) > abs(diffY):
                        if np.sign(diffX) == 1: x1 = x2 = max(x1, x2) # right
                        else: x1 = x2 = min(x1, x2) # left
                        
                    elif abs(diffX) < abs(diffY):
                        if np.sign(diffY) == 1: y1 = y2 = max(y1, y2) # down
                        else: y1 = y2 = min(y1, y2) # up
        
        if abs(diffX) > abs(diffY): # sideward
            if np.sign(diffX) == 1: p = position.x + np.sign(position.x - x2) * arrowWidth * 2 #right  
            else: p = position.x + np.sign(position.x - x1) * arrowWidth * 2 #left
                
            if absoluteSizeY > 0:
                absoluteSize = absoluteSizeY
                
                self.absoluteSize.set(absoluteSizeY)

                if dimensionSelectionType == "Point" or drawingType == "Line" or drawingType == "Arc":
                    line1StartX = x1
                    line1StartY = line1EndY = y1
                    
                    line2StartX = x2
                    line2StartY = line2EndY = y2
                else:
                    line1StartY = line1EndY = y1
                    line2StartY = line2EndY = y2
                    
                    if np.sign(diffX) == 1: line1StartX = line2StartX = x2 #right
                    else: line1StartX = line2StartX = x1 #left
                        
                line1EndX = line2EndX = p
                        
                line1 = canvas.create_line(line1StartX * scaleFactor, line1StartY * scaleFactor, line1EndX * scaleFactor, line1EndY * scaleFactor, tags=tags, fill=fill, width=self.outlineWidth.get())
                line2 = canvas.create_line(line2StartX * scaleFactor, line2StartY * scaleFactor, line2EndX * scaleFactor, line2EndY * scaleFactor, tags=tags, fill=fill, width=self.outlineWidth.get())
                    
                angle = math.degrees(math.atan2(-diffX, 0))
                
                textPosX = position.x
                textPosY = midpointY
                
                arrow1StartX = arrow2StartX = position.x

                arrow1StartY = min(y1, y2)
                arrow2StartY = max(y1, y2)
                
                if self.useCustomLabel.get(): dimensionLabel = self.customLabel.get()
                else: dimensionLabel = f"{round(Dimension._convertPx(absoluteSize, unit), 4)}"
                
                text = canvas.create_text(
                    textPosX * scaleFactor, 
                    textPosY * scaleFactor, 
                    text=dimensionLabel, 
                    tags=tags, 
                    fill=fill, 
                    font=customFont, 
                    angle=angle
                )
                
                textWidth = customFont.measure(dimensionLabel) + 8
                
                textBbox = canvas.bbox(text)                
                
                # arrow1EndX = textPosX + textWidth / 2 * math.cos(math.radians(angle))
                # arrow1EndY = textPosY - textWidth / 2 * math.sin(math.radians(angle))
                
                if min(y1, y2) * scaleFactor < textBbox[1] and max(y1, y2) * scaleFactor > textBbox[3]:
                    arrow1 = canvas.create_line(position.x * scaleFactor, min(y1, y2) * scaleFactor, position.x * scaleFactor, textBbox[1], tags=tags, fill=fill, arrow=FIRST, arrowshape=arrowShape, width=self.outlineWidth.get())
                    arrow2 = canvas.create_line(position.x * scaleFactor, max(y1, y2) * scaleFactor, position.x * scaleFactor, textBbox[3], tags=tags, fill=fill, arrow=FIRST, arrowshape=arrowShape, width=self.outlineWidth.get())
        elif abs(diffX) < abs(diffY): # upward / downward
            if absoluteSizeX > 0:
                absoluteSize = absoluteSizeX
                
                self.absoluteSize.set(absoluteSizeX)
                
                if np.sign(diffX) == 1: p = position.y + np.sign(position.y - y2) * arrowWidth * 2 #right
                else: p = position.y + np.sign(position.y - y1) * arrowWidth * 2 #left
                
                if dimensionSelectionType == "Point" or drawingType == "Line" or drawingType == "Arc":
                    line1StartY = y1
                    line1StartX = line1EndX = x1
                    
                    line2StartY = y2
                    line2StartX = line2EndX = x2
                else:
                    line1StartX = line1EndX = x1
                    line2StartX = line2EndX = x2
                    
                    if np.sign(diffY) == 1: line1StartY = line2StartY = y2
                    else: line1StartY = line2StartY = y1
                
                line1EndY = line2EndY = p
                
                line1 = canvas.create_line(line1StartX * scaleFactor, line1StartY * scaleFactor, line1EndX * scaleFactor, line1EndY * scaleFactor, tags=tags, fill=fill, width=self.outlineWidth.get())
                line2 = canvas.create_line(line2StartX * scaleFactor, line2StartY * scaleFactor, line2EndX * scaleFactor, line2EndY * scaleFactor, tags=tags, fill=fill, width=self.outlineWidth.get())
                
                angle = math.degrees(math.atan2(0, -diffY))
                
                textPosX = midpointX
                textPosY = position.y
                
                arrow1StartX = min(x1, x2)
                arrow1StartY = arrow2StartY = position.y
                arrow2StartX = max(x1, x2)
                
                if self.useCustomLabel.get(): dimensionLabel = self.customLabel.get()
                else: dimensionLabel = f"{round(Dimension._convertPx(absoluteSize, unit), 4)}"
                
                text = canvas.create_text(
                    textPosX * scaleFactor, 
                    textPosY * scaleFactor, 
                    text=dimensionLabel, 
                    tags=tags, 
                    fill=fill, 
                    font=customFont, 
                    angle=angle
                )
                
                textWidth = customFont.measure(dimensionLabel) + 8
                
                textBbox = canvas.bbox(text)                
                
                if min(x1, x2) * scaleFactor < textBbox[0] and max(x1, x2) * scaleFactor > textBbox[2]:
                    arrow1 = canvas.create_line(min(x1, x2) * scaleFactor, position.y * scaleFactor, textBbox[0], position.y * scaleFactor, tags=tags, fill=fill, arrow=FIRST, arrowshape=arrowShape, width=self.outlineWidth.get())
                    arrow2 = canvas.create_line(max(x1, x2) * scaleFactor, position.y * scaleFactor, textBbox[2], position.y * scaleFactor, tags=tags, fill=fill, arrow=FIRST, arrowshape=arrowShape, width=self.outlineWidth.get())
        
        if defaultKWArgs["assignId"]:
            self.annotationIds = [i for i in [line1, line2, arrow1, arrow2, text] if not i is None]
        
    def _onDraw(self, canvas=None, **kwargs):   
        defaultKWArgs = {
            "assignId": True,
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        canvas = Drawing.canvas if canvas is None else canvas
        canvas.delete("prediction")
        
        self.createAnnotation(self.referencePoint, canvas, tags="dimension", fill="red", assignId=defaultKWArgs["assignId"], scaleFactor=defaultKWArgs["scaleFactor"])
        
    def _onPredict(self, nextPoint):
        canvas = Dimension.canvas
        canvas.delete("prediction")
        
        globalVars = Dimension.globalVars
        
        zoom = globalVars.zoom.get() / 100
        
        self.createAnnotation(nextPoint, tags="prediction", fill="blue", scaleFactor=zoom)

        self.referencePoint = nextPoint

class AlignedDimension(Dimension):
    def __init__(self, **kwargs):
        super().__init__("Aligned", **kwargs)
        
    def createAnnotation(self, position, canvas=None, **kwargs):   
        defaultKWArgs = {
            "assignId": True,
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        kwargs = defaultKWArgs
        
        canvas = Dimension.canvas if canvas is None else canvas
        
        globalVars = Dimension.globalVars
        arrowShape = globalVars.dimensionArrowShape
        
        tags = kwargs["tags"] if "tags" in kwargs else ""
        fill = kwargs["fill"] if "fill" in kwargs else "black"
        scaleFactor = kwargs["scaleFactor"]
        
        dimensionSelectionType = Dimension.globalVars.dimensionSelectionType.get()
        unit = Dimension.globalVars.unit.get()
        
        bbox = None
        x1 = None
        y1 = None
        x2 = None
        y2 = None
        
        absoluteSizeX = None
        absoluteSizeY = None
        
        line1 = None
        line2 = None
        arrow1 = None
        arrow2 = None
        text = None
        
        line1StartX = line1StartY = line1EndY = line2StartX = line2StartY = line2EndY = line1EndX = line2EndX = None
        arrow1StartX = arrow1StartY = arrow1EndY = arrow2StartX = arrow2StartY = arrow2EndY = arrow1EndX = arrow2EndX = None
        
        drawingType = ""
        
        if dimensionSelectionType == "Drawing":
            if self.drawing:
                drawingType = self.drawing.type.get()
                
                match drawingType:
                    case "Circle":
                        _p = self.drawing.getPoints()
                        x1 = self.drawing.center.x - self.drawing.absoluteRadius.get()
                        y1 = self.drawing.center.y - self.drawing.absoluteRadius.get()
                        x2 = self.drawing.center.x + self.drawing.absoluteRadius.get()
                        y2 = self.drawing.center.y + self.drawing.absoluteRadius.get()
                    case _:
                        _p = self.drawing.getPoints()
                        x1 = _p[0].x
                        x2 = _p[1].x
                        y1 = _p[0].y
                        y2 = _p[1].y

                absoluteSizeX, absoluteSizeY = self.drawing.absoluteSize()
                
        elif dimensionSelectionType == "Point":
            if len(self._points) >= 2:
                x1 = self._points[0].x
                y1 = self._points[0].y
                x2 = self._points[1].x
                y2 = self._points[1].y
                
                absoluteSizeX = abs(x2 - x1)
                absoluteSizeY = abs(y2 - y1)
                
        customFont = font.Font(
            family=globalVars.dimensionTextFontFamily.get(), 
            size=int(globalVars.dimensionTextFontSize.get() * scaleFactor), 
            weight=globalVars.dimensionTextFontWeight.get(), 
            slant=globalVars.dimensionTextSlant.get()
        )
        
        midpointX = (x1 + x2) / 2
        midpointY = (y1 + y2) / 2
        
        diffX = position.x - midpointX
        diffY = position.y - midpointY
        
        arrowWidth = arrowShape[2]
        
        slope = 0
        
        if self.drawing:
            match drawingType:
                case "Circle": 
                    if abs(diffX) > abs(diffY): x1 = x2 = self.drawing.center.x # sideward
                    elif abs(diffX) < abs(diffY): y1 = y2 = self.drawing.center.y # upward / downward
                    
                case "Rectangle":
                    if abs(diffX) > abs(diffY):
                        if np.sign(diffX) == 1: x1 = x2 = max(x1, x2) # right
                        else: x1 = x2 = min(x1, x2) # left
                        
                    elif abs(diffX) < abs(diffY):
                        if np.sign(diffY) == 1: y1 = y2 = max(y1, y2) # down
                        else: y1 = y2 = min(y1, y2) # up
                    
        line1StartX = x1
        line1StartY = y1
        line2StartX = x2
        line2StartY = y2
            
        midpointX = (x1 + x2) / 2
        midpointY = (y1 + y2) / 2
        
        diffX = position.x - midpointX
        diffY = position.y - midpointY
                    
        rise = y2 - y1
        run = x2 - x1
        
        if run == 0: slope = math.inf
        else: slope = -rise / run
        
        if slope == 0: 
            # horizontal
            line1EndX = x1
            line1EndY = position.y
            
            line2EndX = x2
            line2EndY = position.y
        else: 
            # diagonal
            line1EndX = (x1 + diffX)
            line1EndY = (1/slope * (diffX) + y1)
            
            line2EndX = (x2 + diffX)
            line2EndY = (1/slope * (diffX) + y2)
        
        normalRise = line1EndY - line1StartY
        normalRun = line1EndX - line1StartX
                    
        extensionX = arrowWidth * 2 * math.cos(math.atan2(normalRise, normalRun))
        extensionY = arrowWidth * 2 * math.sin(math.atan2(normalRise, normalRun))
            
        line1 = canvas.create_line(line1StartX * scaleFactor, line1StartY * scaleFactor, (line1EndX + extensionX) * scaleFactor, (line1EndY + extensionY) * scaleFactor, tags=tags, fill=fill, width=self.outlineWidth.get())
        line2 = canvas.create_line(line2StartX * scaleFactor, line2StartY * scaleFactor, (line2EndX + extensionX) * scaleFactor, (line2EndY + extensionY) * scaleFactor, tags=tags, fill=fill, width=self.outlineWidth.get())

        if math.isinf(slope): 
            angle = math.degrees(math.atan2(-diffX, 0))
        elif slope == 0: 
            angle = math.degrees(math.atan2(0, -diffY))
        else: 
            angle = math.degrees(math.atan(slope))
            if 1/slope * (diffX) > 0:
                angle += 180
                
        self.absoluteSize.set(math.hypot(x2 - x1, y2 - y1))
        
        textPosX = (line1EndX + line2EndX) / 2
        textPosY = (line1EndY + line2EndY) / 2
        
        text = canvas.create_text(
            textPosX * scaleFactor, 
            textPosY * scaleFactor, 
            text=f"{round(Dimension._convertPx(self.absoluteSize.get(), unit), 4)}", 
            tags=tags, fill=fill, 
            font=customFont, 
            angle=angle
        )
        
        textWidth = customFont.measure(canvas.itemcget(text, "text")) + 8
        
        if math.hypot(line2EndX - line1EndX, line2EndY - line1EndY) >= textWidth:
            arrow1StartX = line1EndX
            arrow1StartY = line1EndY
            
            arrow2StartX = line2EndX
            arrow2StartY = line2EndY
            
            determinant = normalRun * (position.y - line1StartY) - normalRise * (position.x - line1StartX)
            
            arrow1EndX = textPosX + textWidth / 2 * math.cos(math.radians(angle)) * -np.sign(determinant)
            arrow1EndY = textPosY - textWidth / 2 * math.sin(math.radians(angle)) * -np.sign(determinant)
            
            arrow2EndX = textPosX - textWidth / 2 * math.cos(math.radians(angle)) * -np.sign(determinant)
            arrow2EndY = textPosY + textWidth / 2 * math.sin(math.radians(angle)) * -np.sign(determinant)

            arrow1 = canvas.create_line(arrow1StartX * scaleFactor, arrow1StartY * scaleFactor, arrow1EndX * scaleFactor, arrow1EndY * scaleFactor, tags=tags, fill=fill, arrow=FIRST, arrowshape=arrowShape, width=self.outlineWidth.get())
            arrow2 = canvas.create_line(arrow2StartX * scaleFactor, arrow2StartY * scaleFactor, arrow2EndX * scaleFactor, arrow2EndY * scaleFactor, tags=tags, fill=fill, arrow=FIRST, arrowshape=arrowShape, width=self.outlineWidth.get())
                
        if defaultKWArgs["assignId"]:
            self.annotationIds = [i for i in [line1, line2, arrow1, arrow2, text] if not i is None]
        
    def _onDraw(self, canvas=None, **kwargs):   
        defaultKWArgs = {
            "assignId": True,
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        kwargs = defaultKWArgs
        
        canvas = Dimension.canvas if canvas is None else canvas
        canvas.delete("prediction")
        
        self.createAnnotation(self.referencePoint, canvas, tags="dimension", fill="red", assignId=defaultKWArgs["assignId"], scaleFactor=defaultKWArgs["scaleFactor"])
        
    def _onPredict(self, nextPoint):
        canvas = Dimension.canvas
        canvas.delete("prediction")
        
        globalVars = Dimension.globalVars
        
        zoom = globalVars.zoom.get() / 100
        
        self.createAnnotation(nextPoint, tags="prediction", fill="blue", scaleFactor=zoom)

        self.referencePoint = nextPoint
        
class RadialDimension(Dimension):
    def __init__(self, **kwargs):
        super().__init__("Radial", **kwargs)
        
    def createAnnotation(self, position, canvas=None, **kwargs):   
        defaultKWArgs = {
            "assignId": True,
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        kwargs = defaultKWArgs
        
        canvas = Dimension.canvas if canvas is None else canvas

        globalVars = Dimension.globalVars
        arrowShape = globalVars.dimensionArrowShape
        
        tags = kwargs["tags"] if "tags" in kwargs else ""
        fill = kwargs["fill"] if "fill" in kwargs else "black"
        scaleFactor = kwargs["scaleFactor"]
        
        dimensionSelectionType = Dimension.globalVars.dimensionSelectionType.get()
        unit = Dimension.globalVars.unit.get()
        
        bbox = None
        x1 = None
        y1 = None
        x2 = None
        y2 = None
        absoluteSizeX = None
        absoluteSizeY = None
        
        line1 = None
        line2 = None
        arrow1 = None
        arrow2 = None
        text = None
        
        customFont = font.Font(
            family=globalVars.dimensionTextFontFamily.get(), 
            size=int(globalVars.dimensionTextFontSize.get() * scaleFactor), 
            weight=globalVars.dimensionTextFontWeight.get(), 
            slant=globalVars.dimensionTextSlant.get()
        )
        
        drawingType = ""
        
        if dimensionSelectionType == "Drawing":
            if self.drawing:
                drawingType = self.drawing.type.get()
                
                if drawingType == "Circle" or drawingType == "Arc":
                    centerX = self.drawing.center.x
                    centerY = self.drawing.center.y
                    
                    absoluteRadius = self.drawing.absoluteRadius.get()
                    radius = self.drawing.radius.get()
                    
                    self.absoluteSize.set(absoluteRadius)
                    
                    diffX = position.x - centerX
                    diffY = position.y - centerY
                    
                    try: slope = -diffY / diffX
                    except ZeroDivisionError: slope = math.inf

                    magnitude = math.hypot(diffX, diffY)
                    
                    angle = math.degrees(math.atan2(-diffY, diffX))
                    
                    if angle < 0: angle += 360
                    
                    snappedAngle = angle
                    
                    # midpointX = (centerX + centerX + absoluteRadius * math.cos(math.radians(angle))) / 2
                    # midpointY = (centerY + centerY - absoluteRadius * math.sin(math.radians(angle))) / 2
                    
                    if drawingType == "Arc":
                        start = self.drawing.start.get()
                        end = self.drawing.end.get()
                        
                        if start < 0: start += 360
                        if end < 0: end += 360
                        
                        if angle < min(start, end):
                            snappedAngle = min(start, end)
                        elif angle > max(start, end):
                            snappedAngle = max(start, end)
                            
                    midpointX = (centerX + centerX + absoluteRadius * math.cos(math.radians(snappedAngle))) / 2
                    midpointY = (centerY + centerY - absoluteRadius * math.sin(math.radians(snappedAngle))) / 2
                   
                    if magnitude > absoluteRadius: # position is outside the circle
                        text = canvas.create_text(
                            position.x * scaleFactor, 
                            position.y * scaleFactor, 
                            text=f"R{round(self.drawing.radius.get(), 4)}", 
                            tags=tags, fill=fill, 
                            font=customFont, 
                        )
                        
                        textWidth = customFont.measure(canvas.itemcget(text, "text")) + 8
                        textHeight = customFont.metrics("linespace") + 8
                        
                        line1StartX = centerX + absoluteRadius * math.cos(math.radians(snappedAngle))
                        line1StartY = centerY - absoluteRadius * math.sin(math.radians(snappedAngle))
                        
                        line1EndX = position.x - textWidth/2 * math.cos(math.radians(angle))
                        line1EndY = position.y + textHeight/2 * math.sin(math.radians(angle))
                        
                        line1 = canvas.create_line(line1StartX * scaleFactor, line1StartY * scaleFactor, line1EndX * scaleFactor, line1EndY * scaleFactor, tags=tags, fill=fill, width=self.outlineWidth.get())
                        arrow1 = canvas.create_line(line1StartX * scaleFactor, line1StartY * scaleFactor, centerX * scaleFactor, centerY * scaleFactor, tags=tags, fill=fill, arrow=FIRST, arrowshape=arrowShape, width=self.outlineWidth.get())
                    else:   
                        text = canvas.create_text(
                            midpointX * scaleFactor, 
                            midpointY * scaleFactor, 
                            text=f"R{round(self.drawing.radius.get(), 4)}", 
                            tags=tags, fill=fill, 
                            font=customFont, 
                            angle=snappedAngle
                        )
                        
                        textWidth = customFont.measure(canvas.itemcget(text, "text")) + 8
                        arrow1EndX = midpointX * scaleFactor - textWidth/2 * math.cos(math.radians(snappedAngle))
                        arrow1EndY = midpointY * scaleFactor + textWidth/2 * math.sin(math.radians(snappedAngle))
                        
                        arrow2StartX = centerX + absoluteRadius * math.cos(math.radians(snappedAngle))
                        arrow2StartY = centerY - absoluteRadius * math.sin(math.radians(snappedAngle))
                        
                        arrow2EndX = (midpointX * scaleFactor + textWidth/2 * math.cos(math.radians(snappedAngle))) 
                        arrow2EndY = (midpointY * scaleFactor - textWidth/2 * math.sin(math.radians(snappedAngle))) 
                        # arrow1 - center to text
                        # arrow2 - circumference to text
                        arrow1 = canvas.create_line(centerX * scaleFactor, centerY * scaleFactor, arrow1EndX, arrow1EndY, tags=tags, fill=fill, arrow=FIRST, arrowshape=arrowShape, width=self.outlineWidth.get())
                        arrow2 = canvas.create_line(arrow2StartX * scaleFactor, arrow2StartY * scaleFactor, arrow2EndX, arrow2EndY, tags=tags, fill=fill, arrow=FIRST, arrowshape=arrowShape, width=self.outlineWidth.get())
        
        if defaultKWArgs["assignId"]:
            self.annotationIds = [i for i in [line1, line2, arrow1, arrow2, text] if not i is None]
                        
    def _onDraw(self, canvas=None, **kwargs):   
        defaultKWArgs = {
            "assignId": True,
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        kwargs = defaultKWArgs
        
        canvas = Dimension.canvas if canvas is None else canvas
        
        canvas.delete("prediction")
        
        self.createAnnotation(self.referencePoint, canvas, tags="dimension", fill="red", assignId=defaultKWArgs["assignId"], scaleFactor=defaultKWArgs["scaleFactor"])
        
    def _onPredict(self, nextPoint):
        canvas = Dimension.canvas
        canvas.delete("prediction")
        
        globalVars = Dimension.globalVars
        
        zoom = globalVars.zoom.get() / 100
        
        self.createAnnotation(nextPoint, tags="prediction", fill="blue", scaleFactor=zoom)

        self.referencePoint = nextPoint
        
    def _unitChanged(self, a, b, c):
        canvas = Dimension.canvas
        
        text = [i for i in self.annotationIds if canvas.type(i) == "text"]
        if len(text) <= 0: return
        text = text[0]
        
        canvas.itemconfig(text, text=f"R{round(Dimension._convertPx(self.absoluteSize.get(), Dimension.globalVars.unit.get()), 4)}")
        
class DiametricDimension(Dimension):
    def __init__(self, **kwargs):
        super().__init__("Diametric", **kwargs)
        
    def createAnnotation(self, position, canvas=None, **kwargs):   
        defaultKWArgs = {
            "assignId": True,
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        kwargs = defaultKWArgs
        
        canvas = Dimension.canvas if canvas is None else canvas
        
        globalVars = Dimension.globalVars
        arrowShape = globalVars.dimensionArrowShape
        
        tags = kwargs["tags"] if "tags" in kwargs else ""
        fill = kwargs["fill"] if "fill" in kwargs else "black"
        scaleFactor = kwargs["scaleFactor"]
        
        dimensionSelectionType = Dimension.globalVars.dimensionSelectionType.get()
        unit = Dimension.globalVars.unit.get()
        
        bbox = None
        x1 = None
        y1 = None
        x2 = None
        y2 = None
        absoluteSizeX = None
        absoluteSizeY = None
        
        line1 = None
        line2 = None
        arrow1 = None
        arrow2 = None
        text = None
        
        customFont = font.Font(
            family=globalVars.dimensionTextFontFamily.get(), 
            size=int(globalVars.dimensionTextFontSize.get() * scaleFactor), 
            weight=globalVars.dimensionTextFontWeight.get(), 
            slant=globalVars.dimensionTextSlant.get()
        )
        
        drawingType = ""
        
        if dimensionSelectionType == "Drawing":
            if self.drawing:
                drawingType = self.drawing.type.get()
                
                if drawingType == "Circle" or drawingType == "Arc":
                    centerX = self.drawing.center.x
                    centerY = self.drawing.center.y
                    
                    absoluteRadius = self.drawing.absoluteRadius.get()
                    radius = self.drawing.radius.get()
                    
                    self.absoluteSize.set(absoluteRadius * 2)
                    
                    diffX = position.x - centerX
                    diffY = position.y - centerY
                    
                    try: slope = -diffY / diffX
                    except ZeroDivisionError: slope = math.inf

                    magnitude = math.hypot(diffX, diffY)
                    
                    angle = math.degrees(math.atan2(-diffY, diffX))
                    
                    if angle < 0: angle += 360
                    
                    snappedAngle = angle
                    
                    if drawingType == "Arc":
                        start = self.drawing.start.get()
                        end = self.drawing.end.get()
                        
                        if start < 0: start += 360
                        if end < 0: end += 360
                        
                        if angle < min(start, end):
                            snappedAngle = min(start, end)
                        elif angle > max(start, end):
                            snappedAngle = max(start, end)
                    
                    # midpointX = (centerX + centerX + absoluteRadius * math.cos(math.radians(angle))) / 2
                    # midpointY = (centerY + centerY - absoluteRadius * math.sin(math.radians(angle))) / 2
                    
                    if magnitude > absoluteRadius: # position is outside the circle
                        text = canvas.create_text(
                            position.x * scaleFactor, 
                            position.y * scaleFactor, 
                            text=f"\u2300{round(self.drawing.radius.get() * 2, 4)}", 
                            tags=tags, fill=fill, 
                            font=customFont, 
                        )
                        
                        textWidth = customFont.measure(canvas.itemcget(text, "text")) + 8
                        textHeight = customFont.metrics("linespace") + 8
                        
                        arrow1StartX = centerX + absoluteRadius * math.cos(math.radians(snappedAngle))
                        arrow1StartY = centerY - absoluteRadius * math.sin(math.radians(snappedAngle))
                        
                        arrow1EndX = centerX + absoluteRadius * math.cos(math.radians(snappedAngle + 180))
                        arrow1EndY = centerY - absoluteRadius * math.sin(math.radians(snappedAngle + 180))
                        
                        line1EndX = position.x - textWidth/2 * math.cos(math.radians(snappedAngle))
                        line1EndY = position.y + textHeight/2 * math.sin(math.radians(snappedAngle))
                        
                        arrow1 = canvas.create_line(arrow1StartX * scaleFactor, arrow1StartY * scaleFactor, line1EndX * scaleFactor, line1EndY * scaleFactor, tags=tags, fill=fill, width=self.outlineWidth.get(), arrow=FIRST, arrowshape=arrowShape,)
                    else:
                        if drawingType == "Arc":
                            start = self.drawing.start.get()
                            end = self.drawing.end.get()
                            
                            if start < 0: start += 360
                            if end < 0: end += 360
                            
                            supAngle = angle + 180
                            if supAngle > 360: supAngle -= 360
                            
                            if angle < min(start, end) or supAngle < min(start, end):
                                snappedAngle = min(start, end)
                            elif angle > max(start, end) or supAngle > max(start, end):
                                snappedAngle = max(start, end)
                            
                        midpointX = (centerX + centerX + absoluteRadius * math.cos(math.radians(snappedAngle))) / 2
                        midpointY = (centerY + centerY - absoluteRadius * math.sin(math.radians(snappedAngle))) / 2

                        def draw():
                            text = canvas.create_text(
                                midpointX * scaleFactor, 
                                midpointY * scaleFactor, 
                                text=f"\u2300{round(self.drawing.radius.get() * 2, 4)}", 
                                tags=tags, fill=fill, 
                                font=customFont, 
                                angle=snappedAngle
                            )
                            
                            textWidth = customFont.measure(canvas.itemcget(text, "text")) + 8
                        
                            arrow1StartX = centerX + absoluteRadius * math.cos(math.radians(snappedAngle + 180))
                            arrow1StartY = centerY - absoluteRadius * math.sin(math.radians(snappedAngle + 180))
                            
                            arrow1EndX = midpointX * scaleFactor - textWidth/2 * math.cos(math.radians(snappedAngle))
                            arrow1EndY = midpointY * scaleFactor + textWidth/2 * math.sin(math.radians(snappedAngle))
                            
                            arrow2StartX = centerX + absoluteRadius * math.cos(math.radians(snappedAngle))
                            arrow2StartY = centerY - absoluteRadius * math.sin(math.radians(snappedAngle))
                            
                            arrow2EndX = (midpointX * scaleFactor + textWidth/2 * math.cos(math.radians(snappedAngle))) 
                            arrow2EndY = (midpointY * scaleFactor - textWidth/2 * math.sin(math.radians(snappedAngle))) 
                            
                            arrow1 = canvas.create_line(arrow1StartX * scaleFactor, arrow1StartY * scaleFactor, arrow1EndX, arrow1EndY, tags=tags, fill=fill, arrow=FIRST, arrowshape=arrowShape, width=self.outlineWidth.get())
                            arrow2 = canvas.create_line(arrow2StartX * scaleFactor, arrow2StartY * scaleFactor, arrow2EndX, arrow2EndY, tags=tags, fill=fill, arrow=FIRST, arrowshape=arrowShape, width=self.outlineWidth.get())
                        
                        if drawingType == "Circle": draw()
                        elif abs(self.drawing.extent) >= 180: draw()
        
        if defaultKWArgs["assignId"]:
            self.annotationIds = [i for i in [line1, line2, arrow1, arrow2, text] if not i is None]
         
    def _onDraw(self, canvas=None, **kwargs):   
        defaultKWArgs = {
            "assignId": True,
            "scaleFactor": 1
        }
        
        defaultKWArgs.update(kwargs)
        
        kwargs = defaultKWArgs
        
        canvas = Dimension.canvas if canvas is None else canvas
        
        canvas.delete("prediction")
        
        self.createAnnotation(self.referencePoint, canvas, tags="dimension", fill="red", assignId=defaultKWArgs["assignId"], scaleFactor=defaultKWArgs["scaleFactor"])
        
    def _onPredict(self, nextPoint):
        canvas = Dimension.canvas
        canvas.delete("prediction")
        
        globalVars = Dimension.globalVars
        
        zoom = globalVars.zoom.get() / 100
        
        self.createAnnotation(nextPoint, tags="prediction", fill="blue", scaleFactor=zoom)

        self.referencePoint = nextPoint
        
    def _unitChanged(self, a, b, c):
        canvas = Dimension.canvas
        
        text = [i for i in self.annotationIds if canvas.type(i) == "text"]
        if len(text) <= 0: return
        text = text[0]
        
        canvas.itemconfig(text, text=f"\u2300{round(Dimension._convertPx(self.absoluteSize.get(), Dimension.globalVars.unit.get()), 4)}")