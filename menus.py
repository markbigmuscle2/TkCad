from tkinter import *
from tkinter import filedialog, font, messagebox, ttk
from PIL import Image, ImageGrab
from contextlib import suppress
from conversions import Conversions
from changeHistory import EraseCommand

import os
import io
import math

class CanvasContextMenu(Menu):
    globalVars = None
    
    def __init__(self, master=None, **kwargs):
        defaultKwArgs = { "tearoff": 0 }
        
        defaultKwArgs.update(kwargs)
        
        super().__init__(master, **defaultKwArgs)
        self.selection = []
        
        def onDelete():
            globalVars = CanvasContextMenu.globalVars
            
            for drawing in self.selection:
                drawing.delete()
                
            globalVars.historyManager.do(EraseCommand(drawings=self.selection))

        self.add_command(label="Delete", accelerator="Del", command=onDelete)
        
    def popup(self, x=0, y=0, **kwargs):
        if "selection" in kwargs:
            self.selection = kwargs["selection"]
            
        self.entryconfig("Delete", state="normal" if len(self.selection) > 0 else "disabled")
        
        self.tk_popup(x, y)
        
class ExportMenu(Toplevel):
    canvas = None
    globalVars = None
    
    def __init(self, master=None, **kwargs):
        defaultKwArgs = { "padx": 4, "pady": 4 }
        defaultKwArgs.update(kwargs)
        
        super().__init__(master, **defaultKwArgs)
        self.previewCanvas = None
        
    def checkDrawing(self):
        entireBbox = self.getEntireBbox()
        if math.isinf(entireBbox[0]):
            messagebox.showerror("Export Failed", "Please draw something!", parent=self)
            return False
        return True
        
    def export(self, **kwargs):
        defaultKwArgs = { 
            "bbox": (0, 0, 0, 0),
            "extension": "", 
            "margin": (0, 0, 0, 0)
        }
        
        defaultKwArgs.update(kwargs)
        
        extension = defaultKwArgs["extension"]
        bbox = defaultKwArgs["bbox"]
        margin = defaultKwArgs["margin"]
        
        previewCanvas = self.previewCanvas

        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        self.update_idletasks()
        
        previewCanvasX = previewCanvas.winfo_rootx()
        previewCanvasY = previewCanvas.winfo_rooty()
        
        top = margin[0]
        left = margin[1]
        bottom = margin[2]
        right = margin[3]
        
        finalWidth = int(width + left + right)
        finalHeight = int(height + top + bottom)
        
        captureBbox = (
            previewCanvasX,
            previewCanvasY,
            previewCanvasX + finalWidth,
            previewCanvasY + finalHeight
        )
        
        img = ImageGrab.grab(bbox=captureBbox)
        img = img.resize((finalWidth, finalHeight), Image.Resampling.LANCZOS)
        
        self.destroy()
        
        filePath = filedialog.asksaveasfilename(
            defaultextension=extension,
            initialfile="Untitled"
        )
        
        img.save(filePath, dpi=(96, 96))
        
    def getEntireBbox(self):
        from geometry import Drawing, Dimension, Point
        
        canvas = ExportMenu.canvas
            
        # create image
        drawingBbox = Drawing.bboxAll()
        dimensionBbox = Dimension.bboxAll()
        pointsBbox = Point.bboxAll()
        
        return (
            min(drawingBbox[0], dimensionBbox[0], pointsBbox[0]),
            min(drawingBbox[1], dimensionBbox[1], pointsBbox[1]),
            max(drawingBbox[2], dimensionBbox[2], pointsBbox[2]),
            max(drawingBbox[3], dimensionBbox[3], pointsBbox[3])
        )
        
    def marginGroup(self, master=None, **kwargs):
        from labeledInputs import LabeledEntry
        
        marginGroup = Frame(master)
        
        marginGroup.grid_columnconfigure(0, weight=1, uniform="_")
        marginGroup.grid_columnconfigure(1, weight=1, uniform="_")
        
        entryConfig = {
            "width": 10
        }
        
        marginTop = LabeledEntry(marginGroup, label="Top:", type="Double", unitVar=self._previewUnit, useUnit=True, windowFocus=self, entryConfig=entryConfig)
        marginTop.grid_columnconfigure(0, weight=1)
        marginTop.grid(row=0, column=0, sticky="nsew")
        
        marginBottom = LabeledEntry(marginGroup, label="Bottom:", type="Double", unitVar=self._previewUnit, useUnit=True, windowFocus=self, entryConfig=entryConfig)
        marginBottom.grid_columnconfigure(0, weight=1)
        marginBottom.grid(row=1, column=0, sticky="nsew")
        
        marginLeft = LabeledEntry(marginGroup, label="Left:", type="Double", unitVar=self._previewUnit, useUnit=True, windowFocus=self, entryConfig=entryConfig)
        marginLeft.grid_columnconfigure(0, weight=1)
        marginLeft.grid(row=0, column=1, sticky="nsew")
        
        marginRight = LabeledEntry(marginGroup, label="Right:", type="Double", unitVar=self._previewUnit, useUnit=True, windowFocus=self, entryConfig=entryConfig)
        marginRight.grid_columnconfigure(0, weight=1)
        marginRight.grid(row=1, column=1, sticky="nsew")
        
        marginTop.onChange.append(self.updateMargin)
        marginBottom.onChange.append(self.updateMargin)
        marginLeft.onChange.append(self.updateMargin)
        marginRight.onChange.append(self.updateMargin)
        
        self._marginTop = marginTop
        self._marginBottom = marginBottom
        self._marginLeft = marginLeft
        self._marginRight = marginRight
        
        return marginGroup
        
    def marginPx(self):
        marginTop = self._marginTop
        marginBottom = self._marginBottom
        marginLeft = self._marginLeft
        marginRight = self._marginRight
        
        return (
            Conversions.convertToAbsoluteSize(marginTop.variable.get(), self._previewUnit.get()),
            Conversions.convertToAbsoluteSize(marginLeft.variable.get(), self._previewUnit.get()),
            Conversions.convertToAbsoluteSize(marginBottom.variable.get(), self._previewUnit.get()),
            Conversions.convertToAbsoluteSize(marginRight.variable.get(), self._previewUnit.get()),
        )
        
    def updateMargin(self, returnPressed=False):
        from geometry import Drawing, Dimension, Point
        
        previewCanvas = self.previewCanvas
        canvas = ExportMenu.canvas
        
        entireBbox = self.getEntireBbox()
        
        zoom = ExportMenu.globalVars.zoom.get() / 100

        width = entireBbox[2] - entireBbox[0]
        height = entireBbox[3] - entireBbox[1]
        
        margin = self.marginPx()
        
        top = margin[0]
        left = margin[1]
        bottom = margin[2]
        right = margin[3]
        
        overlappingObjects = canvas.find_overlapping(
            entireBbox[0]*zoom - left,
            entireBbox[1]*zoom - top,
            entireBbox[2]*zoom + right,
            entireBbox[3]*zoom + bottom
        )
        
        drawings = [Drawing.getDrawingById(i) for i in overlappingObjects if not Drawing.getDrawingById(i) is None]
        dimensions = set([Dimension.getDimensionByAnnotationId(i) for i in overlappingObjects if Dimension.getDimensionByAnnotationId(i) is not None])
        gridLines = [i for i in overlappingObjects if "grid" in canvas.gettags(i)]
        
        previewCanvas.pack()
        
        previewCanvas.config(width=width + left + right, height=height + top + bottom)
        previewCanvas.scan_mark(int(entireBbox[0] - left), int(entireBbox[1] - top))
        previewCanvas.scan_dragto(int(previewCanvas.canvasx(0)), int(previewCanvas.canvasy(0)), gain=1)

        for gridLine in gridLines:
            coords = tuple(map(lambda x: x / zoom, canvas.coords(gridLine)))
            
            if len(coords) == 0: continue
            
            if (coords[0] == 0 and coords[2] == 0) or (coords[1] == 0 and coords[3] == 0):
                previewCanvas.create_line(*coords, tags="origin", fill="#999999")
            else:
                previewCanvas.create_line(*coords, tags="grid", fill="#eeeeee")
                
        for drawing in drawings:
            drawing.previewToOtherCanvas(previewCanvas)
            
        for dimension in dimensions:
            dimension.previewToOtherCanvas(previewCanvas)

class ExportAsImageMenu(ExportMenu):
    def __init__(self, master=None):
        from geometry import Drawing, Dimension, Point
        from customWidgets import LabeledEntry

        try:
            canvas = ExportMenu.canvas
            
            zoom = ExportMenu.globalVars.zoom.get() / 100
            
            # create widget
            super().__init__(master, padx=4, pady=4)
            self.title("Export as Image")
            self._format = StringVar(self, value=".png")
            self._showCenter = BooleanVar(self, value=True)
            self._showGrid = BooleanVar(self, value=True)
            self._showOtherPoints = BooleanVar(self, value=True)
            self._previewScale = DoubleVar(self, value=.5)
            self._previewUnit = StringVar(self, value="in")
            
            # create image
            entireBbox = self.getEntireBbox()

            width = entireBbox[2] - entireBbox[0]
            height = entireBbox[3] - entireBbox[1]
            
            content = Frame(self)
            content.pack()
            
            # settings
            lf1 = Frame(content)
            lf1.pack(side=LEFT, anchor="n", fill="y", expand=True)
            
            group1 = LabelFrame(lf1, text="Format")
            group1.pack(fill="x")
            
            radioButtonGroup1 = Frame(group1)
            radioButtonGroup1.pack(anchor="w")
            
            Radiobutton(radioButtonGroup1, text="PNG", value=".png", variable=self._format).pack(anchor="w", side=LEFT)
            Radiobutton(radioButtonGroup1, text="BMP", value=".bmp", variable=self._format).pack(anchor="w", side=LEFT)
            Radiobutton(radioButtonGroup1, text="JPEG", value=".jpeg", variable=self._format).pack(anchor="w", side=LEFT)
            
            group2 = LabelFrame(lf1, text="Unit")
            group2.pack(fill="x")
            
            radioButtonGroup2 = Frame(group2)
            radioButtonGroup2.pack(anchor="w")
            
            Radiobutton(radioButtonGroup2, text="Inches", value="in", variable=self._previewUnit).pack(anchor="w", side=LEFT)
            Radiobutton(radioButtonGroup2, text="Centimeters", value="cm", variable=self._previewUnit).pack(anchor="w", side=LEFT)
            Radiobutton(radioButtonGroup2, text="Millimeters", value="mm", variable=self._previewUnit).pack(anchor="w", side=LEFT)
            
            group3 = LabelFrame(lf1, text="Grid")
            group3.pack(fill="x")
            
            Checkbutton(group3, text="Show", variable=self._showGrid).pack(anchor="w")
            
            group4 = LabelFrame(lf1, text="Points")
            group4.pack(fill=BOTH, expand=True)
            
            pointsGroup = Frame(group4)
            pointsGroup.pack(anchor="w")
            
            Checkbutton(pointsGroup, text="Show Center", variable=self._showCenter).pack(anchor="w")
            Checkbutton(pointsGroup, text="Show Other Points", variable=self._showOtherPoints).pack(anchor="w")
            
            group5 = LabelFrame(lf1, text="Margin")
            group5.pack(fill=BOTH, expand=True)
            
            marginGroup = self.marginGroup(group5)
            marginGroup.pack(anchor="w", fill=BOTH)
            
            # preview
            lf2 = LabelFrame(content, text="Preview")
            lf2.pack(side=LEFT, anchor="n", fill="y", expand=True)
            
            previewCanvasFrame = Frame(lf2, bg="white", width=width, height=height);
            previewCanvasFrame.pack()
            
            previewCanvas = Canvas(previewCanvasFrame, bg="white", width=width, height=height)

            self.previewCanvas = previewCanvas
            
            buttonsGroup = Frame(self)
            buttonsGroup.pack()
            
            Button(buttonsGroup, text="Export", command=lambda: self.export(extension=self._format.get(), bbox=entireBbox, margin=self.marginPx())).pack(side=LEFT, padx=4)
            Button(buttonsGroup, text="Cancel", command=self.destroy).pack(side=RIGHT, padx=4)
            
            if not self.checkDrawing(): 
                self.destroy()
                return
            
            self.updateMargin()
                
            def toggleCenter(*args):
                if self._showCenter.get():
                    previewCanvas.itemconfig("point && center", state="normal")
                    previewCanvas.itemconfig("point && center", state="normal")
                else:
                    previewCanvas.itemconfig("point && center", state="hidden")
                    previewCanvas.itemconfig("point && center", state="hidden")
                    
            def toggleGrid(*args):
                if self._showGrid.get():
                    previewCanvas.itemconfig("origin", state="normal")
                    previewCanvas.itemconfig("grid", state="normal")
                else:
                    previewCanvas.itemconfig("origin", state="hidden")
                    previewCanvas.itemconfig("grid", state="hidden")
                    
            def toggleOtherPoints(*args):
                if self._showOtherPoints.get():
                    previewCanvas.itemconfig("point && !center", state="normal")
                    previewCanvas.itemconfig("point && !center", state="normal")
                else:
                    previewCanvas.itemconfig("point && !center", state="hidden")
                    previewCanvas.itemconfig("point && !center", state="hidden")
                
            self._showCenter.trace_add("write", toggleCenter)
            self._showGrid.trace_add("write", toggleGrid)
            self._showOtherPoints.trace_add("write", toggleOtherPoints)

        except Exception as e:
            raise e

class ExportAsPDF(ExportMenu):
    def __init__(self, master=None):
        try:
            canvas = ExportMenu.canvas
            
            zoom = ExportMenu.globalVars.zoom.get() / 100
            
            # create widget
            super().__init__(master, padx=4, pady=4)
            self.title("Export as PDF")
            self._format = StringVar(self, value=".pdf")
            self._showCenter = BooleanVar(self, value=True)
            self._showGrid = BooleanVar(self, value=True)
            self._showOtherPoints = BooleanVar(self, value=True)
            self._previewScale = DoubleVar(self, value=.5)
            self._previewUnit = StringVar(self, value="in")
            
            # create image
            entireBbox = self.getEntireBbox()

            width = entireBbox[2] - entireBbox[0]
            height = entireBbox[3] - entireBbox[1]
            
            content = Frame(self)
            content.pack()
            
            # settings
            lf1 = Frame(content)
            lf1.pack(side=LEFT, anchor="n", fill="y", expand=True)
            
            group1 = LabelFrame(lf1, text="Unit")
            group1.pack(fill="x")
            
            radioButtonGroup1 = Frame(group1)
            radioButtonGroup1.pack(anchor="w")
            
            Radiobutton(radioButtonGroup1, text="Inches", value="in", variable=self._previewUnit).pack(anchor="w", side=LEFT)
            Radiobutton(radioButtonGroup1, text="Centimeters", value="cm", variable=self._previewUnit).pack(anchor="w", side=LEFT)
            Radiobutton(radioButtonGroup1, text="Millimeters", value="mm", variable=self._previewUnit).pack(anchor="w", side=LEFT)
            
            group2 = LabelFrame(lf1, text="Grid")
            group2.pack(fill="x")
            
            Checkbutton(group2, text="Show", variable=self._showGrid).pack(anchor="w")
            
            group3 = LabelFrame(lf1, text="Points")
            group3.pack(fill="x")
            
            pointsGroup = Frame(group3)
            pointsGroup.pack(anchor="w")
            
            Checkbutton(pointsGroup, text="Show Center", variable=self._showCenter).pack(anchor="w")
            Checkbutton(pointsGroup, text="Show Other Points", variable=self._showOtherPoints).pack(anchor="w")
            
            group4 = LabelFrame(lf1, text="Margin")
            group4.pack(fill=BOTH, expand=True)
            
            marginGroup = self.marginGroup(group4)
            marginGroup.pack(anchor="w", fill=BOTH)
            
            # preview
            lf2 = LabelFrame(content, text="Preview")
            lf2.pack(side=LEFT, anchor="n", fill="y", expand=True)
            
            previewCanvasFrame = Frame(lf2, bg="white", width=width, height=height);
            previewCanvasFrame.pack()
            
            previewCanvas = Canvas(previewCanvasFrame, bg="white", width=width, height=height)

            self.previewCanvas = previewCanvas
            
            buttonsGroup = Frame(self)
            buttonsGroup.pack()
            
            Button(buttonsGroup, text="Export", command=lambda: self.export(extension=".pdf", bbox=entireBbox, margin=self.marginPx())).pack(side=LEFT, padx=4)
            Button(buttonsGroup, text="Cancel", command=self.destroy).pack(side=RIGHT, padx=4)
            
            if not self.checkDrawing(): 
                self.destroy()
                return
            
            self.updateMargin()
                
            def toggleCenter(*args):
                if self._showCenter.get():
                    previewCanvas.itemconfig("point && center", state="normal")
                    previewCanvas.itemconfig("point && center", state="normal")
                else:
                    previewCanvas.itemconfig("point && center", state="hidden")
                    previewCanvas.itemconfig("point && center", state="hidden")
                    
            def toggleGrid(*args):
                if self._showGrid.get():
                    previewCanvas.itemconfig("origin", state="normal")
                    previewCanvas.itemconfig("grid", state="normal")
                else:
                    previewCanvas.itemconfig("origin", state="hidden")
                    previewCanvas.itemconfig("grid", state="hidden")
                    
            def toggleOtherPoints(*args):
                if self._showOtherPoints.get():
                    previewCanvas.itemconfig("point && !center", state="normal")
                    previewCanvas.itemconfig("point && !center", state="normal")
                else:
                    previewCanvas.itemconfig("point && !center", state="hidden")
                    previewCanvas.itemconfig("point && !center", state="hidden")
                
            self._showCenter.trace_add("write", toggleCenter)
            self._showGrid.trace_add("write", toggleGrid)
            self._showOtherPoints.trace_add("write", toggleOtherPoints)

        except Exception as e:
            raise e
          
class DimensionStyleSettings(Toplevel):
    globalVars = None
    
    def __init__(self, master=None):
        globalVars = DimensionStyleSettings.globalVars
        
        super().__init__(master, padx=4, pady=4)
        self.title("Edit Dimension Text Style")
        
        content = Frame(self)
        content.pack()
        
        previewFontFamily = StringVar(self, value=globalVars.dimensionTextFontFamily.get())
        previewFontSize = IntVar(self, value=globalVars.dimensionTextFontSize.get())
        previewFontWeight = StringVar(self, value=globalVars.dimensionTextFontWeight.get())
        previewSlant = StringVar(self, value=globalVars.dimensionTextSlant.get())
        
        # group 1
        lf1 = LabelFrame(content, text="Style")
        lf1.pack(side=LEFT, anchor="n", fill="y", expand=True)
        
        Label(lf1, text="Family:", justify="left").grid(row=0, column=0, sticky="w")
        fontFamily = ttk.Combobox(lf1, textvariable=previewFontFamily, values=font.families(), width="10")
        fontFamily.grid(row=0, column=1, sticky="w")
        
        Label(lf1, text="Size:", justify="left").grid(row=1, column=0, sticky="w")
        fontSize = ttk.Spinbox(lf1, width=8, from_=1, to=2000, increment=1)
        fontSize.grid(row=1, column=1, sticky="w")
        fontSize.delete(0, END)
        fontSize.insert(0, previewFontSize.get())
        
        Label(lf1, text="Weight:", justify="left").grid(row=2, column=0, sticky="w")
        fontWeight = ttk.Combobox(lf1, textvariable=previewFontWeight, values=["normal", "bold"], state="readonly", width="10")
        fontWeight.grid(row=2, column=1, sticky="w")
        
        Label(lf1, text="Slant:", justify="left").grid(row=3, column=0, sticky="w")
        slant = ttk.Combobox(lf1, textvariable=previewSlant, values=["roman", "italic"], state="readonly", width="10")
        slant.grid(row=3, column=1, sticky="w")
        
        # group 2
        lf2 = LabelFrame(content, text="Preview")
        lf2.pack(side=LEFT, anchor="n")
        
        previewCanvas = Canvas(lf2, bg="white", width=200, height=200)
        previewCanvas.pack()
        
        textPreview = previewCanvas.create_text(100, 100, text="0.123456789 in")
        
        def updateFont(a=None, b=None, c=None):
            previewCanvas.itemconfig(textPreview, font=font.Font(family=previewFontFamily.get(), size=previewFontSize.get(), weight=previewFontWeight.get(), slant=previewSlant.get()))
        
        updateFont()
        
        # events
        previewFontFamily.trace_add("write", updateFont)
        previewFontSize.trace_add("write", updateFont)
        previewFontWeight.trace_add("write", updateFont)
        previewSlant.trace_add("write", updateFont)
        
        def fontSizeChanged(event):
            previewFontSize.set(fontSize.get())
            self.focus_set()
        
        fontSize.bind("<Return>", fontSizeChanged)
        fontSize.bind("<<Increment>>", fontSizeChanged)
        fontSize.bind("<<Decrement>>", fontSizeChanged)
        
        # buttons
        buttonsGroup = Frame(self)
        buttonsGroup.pack(pady=4)
        
        def applyCommand():
            from geometry import Dimension
            
            globalVars.dimensionTextFontFamily.set(previewFontFamily.get())
            globalVars.dimensionTextFontSize.set(previewFontSize.get())
            globalVars.dimensionTextFontWeight.set(previewFontWeight.get())
            globalVars.dimensionTextSlant.set(previewSlant.get())
            
            with suppress(Exception):
                Dimension.redrawAll()
            
            self.destroy()
        
        Button(buttonsGroup, text="Apply", command=applyCommand).pack(side=LEFT, padx=4)
        Button(buttonsGroup, text="Cancel", command=self.destroy).pack(side=RIGHT, padx=4)