from geometry import *
from contextlib import suppress

class Tool:
    canvas = None
    globalVars = None
    propertyMenu = None
    
    def __init__(self, name, modeNames = []):
        from tkinter import IntVar
        
        self.mode = IntVar(value=0) # default mode is 0
        self.modeName = StringVar(value="Default")
        self.modeNames = modeNames
        self.name = name
        
        def modeChanged(*args):
            if len(self.modeNames) == 0: self.modeName.set("Default")
            else: self.modeName.set(self.modeNames[self.mode.get()])
        
        self.mode.trace_add("write", modeChanged)
        
        modeChanged()
        
    def createPointPosition(self, fill="blue"):
        with suppress(Exception):
            canvas = Tool.canvas
            globalVars = Tool.globalVars
            
            r = globalVars.pointRadius.get()
            
            zoom = globalVars.zoom.get()/100
            
            canvas.delete("pointPosition")
            
            canvas.create_oval(-r * zoom, -r * zoom, r * zoom, r * zoom, fill=fill, tags="pointPosition", outline="")
        
    def _convertToAbsoluteSize(self, value=0, unit="px"): 
        globalVars = Tool.globalVars
        ppi = globalVars.ppi.get()
        
        if unit == "in":
            return float(Decimal(str(value)) * Decimal(str(ppi)))
        elif unit == "cm":
            return float(Decimal(str(value)) * Decimal(str(ppi)) / Decimal(str(2.54)))
        elif unit == "mm":
            return float(Decimal(str(value)) * Decimal(str(ppi)) / Decimal(str(25.4)))
        return value
        
    def finish(self):
        textAnnotation = Tool.globalVars.fixedTextAnnotation
        
        canvas = Tool.canvas

        canvas.delete("pointPosition")
        
        textAnnotation.text.set("")
        textAnnotation.hide()
        
        if hasattr(self, "_finish"): self._finish()
        
    def _movePointCursor(self, event, snapToGrid = False):
        globalVars = Tool.globalVars
        
        canvas = Tool.canvas
        canvasCursorPos = globalVars.canvasCursorPosition
        convertToAbsoluteSize = self._convertToAbsoluteSize
        zoom = globalVars.zoom.get()/100
        
        gridSize = convertToAbsoluteSize(globalVars.gridSize.get(), globalVars.unit.get())
        zoomedGridSize = convertToAbsoluteSize(globalVars.gridSize.get(), globalVars.unit.get()) * zoom
        
        r = globalVars.pointRadius.get()
        
        pX = canvas.canvasx(event.x)
        pY = canvas.canvasy(event.y)
        
        canvas.itemconfig("pointPosition", state="hidden")
        canvas.itemconfig("prediction", state="hidden")

        t = canvas.find_closest(canvas.canvasx(event.x), canvas.canvasy(event.y), halo=r)
        
        if snapToGrid:
            pX = float(Decimal(str(gridSize)) * Decimal(str(round(pX / zoomedGridSize))))
            pY = float(Decimal(str(gridSize)) * Decimal(str(round(pY / zoomedGridSize))))
        else:
            pX = round(pX / zoom)
            pY = round(pY / zoom)
        
        if len(t) > 0:
            isPoint = "point" in canvas.gettags(*t)
            
            if isPoint and globalVars.snapToPoint.get():
                p = Point.getPointInCanvasById(*t)
                pX = p.x
                pY = p.y
                
        canvas.itemconfig("pointPosition", state="normal")
        canvas.itemconfig("prediction", state="normal")
            
        canvas.moveto("pointPosition", round((pX - r) * zoom), round((pY - r) * zoom))
        
        canvasCursorPos.set(pX, pY)
            
        return Point(pX, pY)
        
    def showDistanceFromLastPoint(self):
        pass
        
    def start(self):
        canvas = Tool.canvas
        globalVars = Tool.globalVars
        
        dimensionSelectionType = globalVars.dimensionSelectionType.get()
        
        r = globalVars.pointRadius.get()
    
        globalVars.toolActivatedCounter.set(0)
        
        zoom = globalVars.zoom.get()/100

        canvas.delete("prediction")

        if globalVars.currentDrawing:
            del globalVars.currentDrawing
            globalVars.currentDrawing = None
            
        if globalVars.currentDimension:
            del globalVars.currentDimension
            globalVars.currentDimension = None
            
        canvas.config(cursor="")
        
        if hasattr(self, "_start"): self._start()
        
        Tool.propertyMenu.clearSelection()
        
    def toolActivated(self, event, ctrlKeyPressed=False):
        if hasattr(self, "_toolActivated"): self._toolActivated(event, ctrlKeyPressed)
       
    def toolBtn1Down(self, event, ctrlKeyPressed=False):
        if hasattr(self, "_toolBtn1Down"): self._toolBtn1Down(event, ctrlKeyPressed)
        
    def toolBtn1Motion(self, event, ctrlKeyPressed=False):
        if hasattr(self, "_toolBtn1Motion"): self._toolBtn1Motion(event, ctrlKeyPressed)
        
    def toolMotion(self, event, ctrlKeyPressed=False):
        if hasattr(self, "_toolMotion"): self._toolMotion(event, ctrlKeyPressed)
        
class ArcTool(Tool):
    def __init__(self, modeNames = []):
        super().__init__("Arc", modeNames)
        
    def _start(self):
        self.createPointPosition()
        
    def _toolActivated(self, event, ctrlKeyPressed=False):
        canvas = Tool.canvas
        globalVars = Tool.globalVars
        
        canvasCursorPosition = globalVars.canvasCursorPosition
        counter = globalVars.toolActivatedCounter.get()
        textAnnotation = globalVars.fixedTextAnnotation

        pX = canvasCursorPosition.x.get()
        pY = canvasCursorPosition.y.get()
        p = Point(pX, pY)
        
        if counter == 0:
            textAnnotation.text.set("")
            textAnnotation.show()
            
            counter += 1
            globalVars.currentDrawing = Arc()
            globalVars.currentDrawing.setCenter(CenterMark(pX, pY))
        elif counter == 1:
            textAnnotation.hide()
            counter += 1
            globalVars.currentDrawing.startPoint.setPosition(pX, pY)
        elif counter == 2:
            counter = 0
            
            arc = globalVars.currentDrawing

            pX = arc.center.x + arc.absoluteRadius.get() * math.cos(math.radians(arc.end.get()))
            pY = arc.center.y - arc.absoluteRadius.get() * math.sin(math.radians(arc.end.get()))
            
            globalVars.currentDrawing.endPoint.setPosition(pX, pY)
            globalVars.currentDrawing.draw()
            
            del globalVars.currentDrawing
            globalVars.currentDrawing = None
            
        globalVars.toolActivatedCounter.set(counter)
        
    def _toolMotion(self, event, ctrlKeyPressed=False):
        globalVars = Tool.globalVars
        textAnnotation = globalVars.fixedTextAnnotation
        
        canvas = Tool.canvas
        movePointCursor = self._movePointCursor
        
        counter = globalVars.toolActivatedCounter.get()
        
        p = movePointCursor(event, globalVars.snapToGrid.get())

        if globalVars.currentDrawing:
            match counter:
                case 1: textAnnotation.text.set(f"Radius:\n{globalVars.currentDrawing.radius.get()} {globalVars.unit.get()}")
                case 2: p = movePointCursor(event)
                
            globalVars.currentDrawing.predict(p)

class CircleTool(Tool):
    def __init__(self, modeNames = []):
        super().__init__("Circle", modeNames)
        
    def _start(self):
        self.createPointPosition()
        
    def _toolActivated(self, event, ctrlKeyPressed=False):
        canvas = Tool.canvas
        globalVars = Tool.globalVars
        
        canvasCursorPosition = globalVars.canvasCursorPosition
        counter = globalVars.toolActivatedCounter.get()
        textAnnotation = globalVars.fixedTextAnnotation

        pX = canvasCursorPosition.x.get()
        pY = canvasCursorPosition.y.get()
        p = Point(pX, pY)
        
        toolMode = self.mode.get()
        
        if toolMode == 0: # center, point
            if counter == 0:
                textAnnotation.text.set("")
                textAnnotation.show()
            
                counter += 1
                globalVars.currentDrawing = Circle(mode=toolMode)
                globalVars.currentDrawing.setCenter(CenterMark(pX, pY))
            elif counter == 1:
                textAnnotation.hide()
                
                counter = 0
                globalVars.currentDrawing.draw()
                globalVars.currentDrawing = None
        elif toolMode == 1:
            if counter == 0:
                textAnnotation.text.set("")
                textAnnotation.show()
                
                counter += 1
                globalVars.currentDrawing = Circle(mode=toolMode)
                globalVars.currentDrawing.addPoint(p)
            elif counter == 1:
                textAnnotation.hide()
                
                counter = 0
                globalVars.currentDrawing.addPoint(p)
                globalVars.currentDrawing.draw()
                globalVars.currentDrawing = None
            
        globalVars.toolActivatedCounter.set(counter)
        
    def _toolMotion(self, event, ctrlKeyPressed=False):
        globalVars = Tool.globalVars
        
        movePointCursor = self._movePointCursor
        
        counter = globalVars.toolActivatedCounter.get()
        textAnnotation = globalVars.fixedTextAnnotation
        
        toolMode = self.mode.get()
        
        p = movePointCursor(event, globalVars.snapToGrid.get())
            
        if globalVars.currentDrawing:
            match toolMode:
                case 0: 
                    if counter == 1: textAnnotation.text.set(f"Radius:\n{globalVars.currentDrawing.radius.get()} {globalVars.unit.get()}")
                case 1: 
                    if counter == 1: textAnnotation.text.set(f"Diameter:\n{globalVars.currentDrawing.radius.get() * 2} {globalVars.unit.get()}")
                    
            globalVars.currentDrawing.predict(p)
        
class DimensionTool(Tool):
    def __init__(self, modeNames = []):
        super().__init__("Dimension", modeNames)
        
    def _start(self):
        canvas = Tool.canvas
        globalVars = Tool.globalVars
        
        dimensionSelectionType = globalVars.dimensionSelectionType.get()
        
        if dimensionSelectionType == "Drawing":
            canvas.config(cursor="cross")
        elif dimensionSelectionType == "Point":
            self.createPointPosition()
            
    def _toolActivated(self, event, ctrlKeyPressed=False):
        canvas = Tool.canvas
        globalVars = Tool.globalVars
        
        canvasCursorPosition = globalVars.canvasCursorPosition
        counter = globalVars.toolActivatedCounter.get()
        zoom = globalVars.zoom.get()/100
        
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)

        pX = canvasCursorPosition.x.get()
        pY = canvasCursorPosition.y.get()
        
        p = Point(pX, pY)
        
        drawings = [Drawing.getDrawingById(drawingId) for drawingId in canvas.find_closest(x, y) if not Drawing.getDrawingById(drawingId) is None]
        dimensionMode = self.mode.get()
        dimensionSelectionType = Tool.globalVars.dimensionSelectionType.get()
        
        if dimensionMode == 0: # linear
            if dimensionSelectionType == "Drawing":
                if counter == 0:
                    if len(drawings) > 0:
                        drawing = drawings[0]

                        globalVars.currentDimension = LinearDimension()
                        globalVars.currentDimension.drawing = drawing
                        
                        counter += 1
                elif counter == 1:
                    globalVars.currentDimension.draw()
                    counter = 0
            elif dimensionSelectionType == "Point":
                if counter == 0:
                    globalVars.currentDimension = LinearDimension()
                    
                    globalVars.currentDimension.addPoint(p)
                    counter += 1
                elif counter == 1:
                    globalVars.currentDimension.addPoint(p)
                    counter += 1
                elif counter == 2:
                    globalVars.currentDimension.draw()
                    counter = 0
        elif dimensionMode == 1: # aligned
            if dimensionSelectionType == "Drawing":
                if counter == 0:
                    if len(drawings) > 0:
                        drawing = drawings[0]

                        globalVars.currentDimension = AlignedDimension()
                        globalVars.currentDimension.drawing = drawing
                        
                        counter += 1
                elif counter == 1:
                    globalVars.currentDimension.draw()
                    counter = 0
            elif dimensionSelectionType == "Point":
                if counter == 0:
                    globalVars.currentDimension = AlignedDimension()
                    
                    globalVars.currentDimension.addPoint(p)
                    counter += 1
                elif counter == 1:
                    globalVars.currentDimension.addPoint(p)
                    counter += 1
                elif counter == 2:
                    globalVars.currentDimension.draw()
                    counter = 0
        elif dimensionMode == 2: # radial
            if dimensionSelectionType == "Drawing":
                if counter == 0:
                    if len(drawings) > 0:
                        drawing = drawings[0]

                        globalVars.currentDimension = RadialDimension()
                        globalVars.currentDimension.drawing = drawing
                        
                        counter += 1
                elif counter == 1:
                    globalVars.currentDimension.draw()
                    counter = 0
        elif dimensionMode == 3: # diametric
            if dimensionSelectionType == "Drawing":
                if counter == 0:
                    if len(drawings) > 0:
                        drawing = drawings[0]

                        globalVars.currentDimension = DiametricDimension()
                        globalVars.currentDimension.drawing = drawing
                        
                        counter += 1
                elif counter == 1:
                    globalVars.currentDimension.draw()
                    counter = 0
                
        globalVars.toolActivatedCounter.set(counter)
        
    def _toolMotion(self, event, ctrlKeyPressed=False):
        globalVars = Tool.globalVars
        
        dimensionSelectionType = globalVars.dimensionSelectionType.get()
        movePointCursor = self._movePointCursor

        if dimensionSelectionType == "Drawing":
            p = movePointCursor(event)
            if globalVars.toolActivatedCounter.get() == 1:
                if globalVars.currentDimension: globalVars.currentDimension.predict(p)
        elif dimensionSelectionType == "Point":
            if globalVars.toolActivatedCounter.get() < 2:
                p = movePointCursor(event, globalVars.snapToGrid.get())
            else:
                p = movePointCursor(event)
                if globalVars.currentDimension: globalVars.currentDimension.predict(p)
        
class EraseTool(Tool):
    def __init__(self, modeNames = []):
        super().__init__("Erase", modeNames)
        
    def _start(self):
        Tool.canvas.config(cursor="circle")
        
    def _toolBtn1Motion(self, event, ctrlKeyPressed=False):
        canvas = Tool.canvas
        globalVars = Tool.globalVars
        
        drawings = [Drawing.getDrawingById(i) for i in canvas.find_closest(canvas.canvasx(event.x), canvas.canvasy(event.y)) if "drawing" in canvas.gettags(i)]
        drawings = [i for i in drawings if not i is None]
        
        dimensions = [Dimension.getDimensionByAnnotationId(i) for i in canvas.find_closest(canvas.canvasx(event.x), canvas.canvasy(event.y)) if "dimension" in canvas.gettags(i)]
        dimensions = [i for i in dimensions if not i is None]
        
        if len(drawings) > 0:
            for drawing in drawings:
                drawing.delete()
                
            globalVars.historyManager.do(EraseCommand(drawings=drawings))
            
        if len(dimensions) > 0:
            for dimension in dimensions:
                dimension.delete()
                
            globalVars.historyManager.do(EraseCommand(drawings=dimensions))
        
class LineTool(Tool):
    def __init__(self, modeNames = []):
        super().__init__("Line", modeNames)
        
    def _start(self):
        self.createPointPosition()
        
    def _toolActivated(self, event, ctrlKeyPressed=False):
        canvas = Tool.canvas
        globalVars = Tool.globalVars
        
        canvasCursorPosition = globalVars.canvasCursorPosition
        counter = globalVars.toolActivatedCounter.get()
        textAnnotation = globalVars.fixedTextAnnotation
        
        pX = canvasCursorPosition.x.get()
        pY = canvasCursorPosition.y.get()
        
        p = Point(pX, pY)
        
        toolMode = self.mode.get()
        
        if counter == 0:
            textAnnotation.text.set("")
            textAnnotation.show()
                
            globalVars.currentDrawing = Line(mode=toolMode)
            
            counter += 1
            
            globalVars.currentDrawing.addPoint(p)
        elif counter == 1:
            textAnnotation.hide()
            
            counter = 0
            
            globalVars.currentDrawing.addPoint(p)
            
            if toolMode == 1:
                points = globalVars.currentDrawing.getPoints()
                
                x1 = points[0].x
                x2 = points[1].x
                y1 = points[0].y
                y2 = points[1].y
                
                centerX = (x1 + x2) / 2
                centerY = (y1 + y2) / 2
                
                globalVars.currentDrawing.setCenter(Point(centerX, centerY))
                
            globalVars.currentDrawing.draw()
            globalVars.currentDrawing = None
            
        globalVars.toolActivatedCounter.set(counter)
        
    def _toolMotion(self, event, ctrlKeyPressed=False):
        globalVars = Tool.globalVars
        movePointCursor = self._movePointCursor
        textAnnotation = globalVars.fixedTextAnnotation
        
        p = movePointCursor(event, globalVars.snapToGrid.get())
            
        if globalVars.currentDrawing:
            textAnnotation.text.set(f"Length:\n{globalVars.currentDrawing.length.get()} {globalVars.unit.get()}")
            globalVars.currentDrawing.predict(p)
        
class PanTool(Tool):
    def __init__(self, modeNames = []):
        super().__init__("Pan", modeNames)
        
    def _start(self):
        Tool.canvas.config(cursor="fleur")
        
    def _toolBtn1Down(self, event, ctrlKeyPressed=False):
        canvas = Tool.canvas
        canvas.scan_mark(event.x, event.y)
        
    def _toolBtn1Motion(self, event, ctrlKeyPressed=False):
        x, y = event.x, event.y
        
        canvas = Tool.canvas
        globalVars = Tool.globalVars
        
        canvas.scan_dragto(x, y, gain=1)
        
        currentX = canvas.canvasx(0)
        currentY = canvas.canvasy(0)
        
        globalVars.viewOffset.set(currentX, currentY)

        if globalVars.showGrid.get():
            globalVars.grid.generate(offsetX=currentX, offsetY=currentY)
        
class RectangleTool(Tool):
    def __init__(self, modeNames = []):
        super().__init__("Rectangle", modeNames)
        
    def _start(self):
        self.createPointPosition()
         
    def _toolActivated(self, event, ctrlKeyPressed=False):
        globalVars = Tool.globalVars
        
        canvasCursorPosition = globalVars.canvasCursorPosition
        counter = globalVars.toolActivatedCounter.get()

        pX = canvasCursorPosition.x.get()
        pY = canvasCursorPosition.y.get()
        
        p = Point(pX, pY)
        
        if counter == 0:
            globalVars.currentDrawing = Rectangle(p)
            
            counter += 1
        elif counter == 1:
            counter = 0
            
            globalVars.currentDrawing.addPoint(p)
            globalVars.currentDrawing.draw()
            globalVars.currentDrawing = None
            
        globalVars.toolActivatedCounter.set(counter)
        
    def _toolMotion(self, event, ctrlKeyPressed=False):
        globalVars = Tool.globalVars
        movePointCursor = self._movePointCursor
        
        p = movePointCursor(event, globalVars.snapToGrid.get())
            
        if globalVars.currentDrawing:
            globalVars.currentDrawing.predict(p)
        
class SelectTool(Tool):
    def __init__(self, modeNames = []):
        super().__init__("Select", modeNames)
        self.selectionBox = None
        
    def _toolBtn1Down(self, event, ctrlKeyPressed=False):
        canvas = Tool.canvas
        globalVars = Tool.globalVars
        
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        
        globalVars.selectionBoxStart.set(x, y)
        
        self.selectionBox = canvas.create_rectangle(x, y, x, y, tags="selectionBox", dash=(12,4), width=2, outline="blue")
        
        objects = canvas.find_overlapping(x, y, x, y)
        drawings = [Drawing.getDrawingById(objectId) for objectId in objects if Drawing.getDrawingById(objectId)]
            
        Tool.propertyMenu.startSelection()
        Tool.propertyMenu.updateSelection(*drawings, ctrlKeyPressed=ctrlKeyPressed)
        
    def _toolBtn1Motion(self, event, ctrlKeyPressed=False):
        canvas = Tool.canvas
        globalVars = Tool.globalVars
        
        selectionStartX, selectionStartY = globalVars.selectionBoxStart.get()
        
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        
        canvas.coords(self.selectionBox, selectionStartX, selectionStartY, x, y)
        
        objects = canvas.find_overlapping(*canvas.coords(self.selectionBox))
        drawings = [Drawing.getDrawingById(objectId) for objectId in objects if Drawing.getDrawingById(objectId)]
            
        Tool.propertyMenu.updateSelection(*drawings, ctrlKeyPressed=ctrlKeyPressed)
        
    def _toolActivated(self, event, ctrlKeyPressed=False):
        canvas = Tool.canvas
        globalVars = Tool.globalVars
        
        canvas.delete(self.selectionBox)
        self.selectionBox = None
        
        Tool.propertyMenu.finishSelection()
        
class TextTool(Tool):
    def __init__(self, modeNames = []):
        super().__init__("Text", modeNames)

    def _finish(self):
        globalVars = Tool.globalVars
        if globalVars.currentDrawing: globalVars.currentDrawing.finishEdit()
        
    def _start(self):
        canvas = Tool.canvas
        canvas.config(cursor="xterm")
        canvas.create_oval(0, 0, 0, 0, tags="pointPosition", outline="")
        
    def _toolActivated(self, event, ctrlKeyPressed=False):
        globalVars = Tool.globalVars
        
        canvasCursorPosition = globalVars.canvasCursorPosition
        counter = globalVars.toolActivatedCounter.get()

        pX = canvasCursorPosition.x.get()
        pY = canvasCursorPosition.y.get()
        
        p = Point(pX, pY)
        
        if globalVars.currentDrawing:
            if globalVars.currentDrawing.type == "Text":
                 globalVars.currentDrawing.finishEdit()
        
        globalVars.currentDrawing = TextDrawing(p)
        globalVars.currentDrawing.draw()
        globalVars.currentDrawing.startEdit()