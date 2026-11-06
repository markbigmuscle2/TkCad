from tkinter import *
from tkinter import ttk
from pathlib import Path
from contextlib import suppress

from changeHistory import *
from conversions import Conversions
from decimal import Decimal
from labeledInputs import *
from menus import *

import canvasTools as ct
import random
import re
import webbrowser

SCRIPT_DIR = Path(__file__).resolve().parent

convertPx = Conversions.convertPx
convertToAbsoluteSize = Conversions.convertToAbsoluteSize

# variables

class Vector2Var(Variable):
    def __init__(self, master=None, x=0, y=0):
        super().__init__(master)
        
        self.x = DoubleVar(master, value=x)
        self.y = DoubleVar(master, value=y)
        
        self.StringVar = StringVar(value=str(self.get()))
        
    def __repr__(self):
        return str(self.get())
       
    def get(self):
        return (self.x.get(), self.y.get())
        
    def set(self, x, y):
        self.x.set(x)
        self.y.set(y)
        self.StringVar.set(str(self.get()))

    def trace_add(self, mode, callback):
        self.x.trace_add(mode, callback)
        self.y.trace_add(mode, callback)
        
    def mapForCanvas(self):
        self.StringVar.set(str((-self.x.get(), self.y.get())))
        
class Vector2IntVar(Vector2Var):
    def __init__(self, master=None, x=0, y=0):
        super().__init__(master)

        self.x = IntVar(master, value=x)
        self.y = IntVar(master, value=y)
        self.StringVar = StringVar(value=str(self.get()))
        
class GlobalVariables:
    def __init__(self, master=None):
        from geometry import Drawing, FixedTextAnnotation
        
        self.master = master
        
        # root
        self.root = None
        
        # grid
        self.grid = None
        self.unit = StringVar(master, value="in")
        self.lastUnit = StringVar(master, value="in")
        self.gridSize = DoubleVar(master, value=0.5)
        self.snapToGrid = BooleanVar(master, value=True)
        self.showGrid = BooleanVar(master, value=True)
        self.ppi = DoubleVar(master, value=96)
        
        # rotation
        self.angleIncrement = DoubleVar(master, value=15.0)
        self.snapToRotate = BooleanVar(master, value=True)
        
        # export image
        self.exportImageResolution = DoubleVar(master, value=72)
        
        # zoom
        self.zoom = DoubleVar(master, value=100)
        self.lastZoom = DoubleVar(master, value=100)
        
        # shift
        self.shiftKeyDown = BooleanVar(master, value=False)
        
        # viewpoint
        self.viewOffset = Vector2IntVar(master, 0, 0)
        self.viewOffsetPanStart = Vector2IntVar(master, 0, 0)
        
        # cursor
        self.canvasCursorPosition = Vector2Var(master, 0, 0)
        
        # tool
        self.lastTool = StringVar(master, value="Select")
        self.tool = StringVar(master, value="Select")
        self.toolActivatedPosition = Vector2IntVar(master, 0, 0)
        self.toolActivatedCounter = IntVar(master, value=0)
        self.toolObject = None
        
        # selection box
        self.selectionBoxStart = Vector2Var(master, 0, 0)
        
        # dimension
        self.dimensionSelectionType = StringVar(master, value="Drawing")
        self.currentDimension = None
        
        self.dimensionTextFontFamily = StringVar(master, value="Arial")
        self.dimensionTextFontSize = IntVar(master, value=14)
        self.dimensionTextFontWeight = StringVar(master, value="normal")
        self.dimensionTextSlant = StringVar(master, value="roman")
        self.dimensionArrowShape = (8, 8, 6)

        # points
        self.pointRadius = IntVar(master, value=4)
        
        self.showCenter = BooleanVar(master, value=True)
        self.showCenter.trace_add("write", lambda a, b, c: Drawing.showAllPoints())
        
        self.showOtherPoints = BooleanVar(master, value=True)
        self.showOtherPoints.trace_add("write", lambda a, b, c: Drawing.showAllPoints())
        
        self.snapToPoint = BooleanVar(master, value=True)
        
        # drawing
        self.currentDrawing = None
        
        # history
        self.historyManager = HistoryManager()

        # style
        self.style = ttk.Style()
        
        s = self.style
        
        # property menu
        self.showPropertyMenu = BooleanVar(master, value=True)
        
        # fixed text annotation
        self.fixedTextAnnotation = FixedTextAnnotation(16, 16, "")
        self.fixedTextAnnotation.hide()
        
        s.configure("QuickAccessToolbarButton.TButton", background="white", borderwidth=0)
        s.configure("Line.TSeparator", background="white")
      
# widgets

# other

class ToolButton(Frame):
    def _update(self, **kwargs):
        if "image" in kwargs:
            self.image = kwargs["image"]
            self._canvas.create_image(20, 20, image=self.image)
            
        if "label" in kwargs:
            self._label.config(text=kwargs["label"])
            
        if "command" in kwargs:
            self.bind("<Button-1>", lambda event: kwargs["command"]())
            self._canvas.bind("<Button-1>", lambda event: kwargs["command"]())
            self._label.bind("<Button-1>", lambda event: kwargs["command"]())
            
        if "state" in kwargs:
            self._state.set(kwargs["state"])
        
    def _mouseLeave(self, event):
        self._update(state="normal")
        
    def _motion(self, event):
        self._update(state="hover")
            
    def __init__(self, master=None, **kwargs):
        defaultKwArgs = { 
            "bg": "white",
            "hoverbg": "SystemActiveBorder",
            "menu": None,
            "state": "normal"
        }
        defaultKwArgs.update(kwargs)
        
        super().__init__(master)
        
        self._canvas = Canvas(self, width=40, height=40, highlightthickness=0)
        self._canvas.pack()
        
        self._label = Label(self, text="ToolButton")
        self._label.pack()
        
        self._dropdownArrow = None
        self._menu = None
        
        if defaultKwArgs["menu"]:
            self._dropdownArrow = Label(self, text="6", font=("Marlett", 10))
            self._dropdownArrow.pack()
            
            self._menu = defaultKwArgs["menu"]
            
            self._dropdownArrow.bind("<Button-1>", lambda event: self._menu.tk_popup(event.x_root, event.y_root))
        
        self._state = StringVar(value=defaultKwArgs["state"])
        
        def changeState():
            if self._state.get() == "normal":
                bg = defaultKwArgs["bg"] or defaultKwArgs["background"]
            elif self._state.get() == "hover":
                bg = defaultKwArgs["hoverbg"] or defaultKwArgs["hoverbackground"]
                
            self.config(bg=bg)
            self._canvas.config(bg=bg)
            self._label.config(bg=bg)
            if self._dropdownArrow: self._dropdownArrow.config(bg=bg)
                
        self._state.trace_add("write", lambda *args: changeState())
        
        changeState()
        
        self._update(**kwargs)
        
        self.bind("<Motion>", self._motion)
        self._canvas.bind("<Motion>", self._motion)
        self._label.bind("<Motion>", self._motion)
        
        self.bind("<Leave>", self._mouseLeave)
            
    def configure(self, cnf=None, **kwargs):
        if cnf is None: cnf = {}
        kwargs.update(cnf)
        
        self._update(**kwargs)
        
        return super().configure(cnf)
        
class QuickAccessToolbarButton(ttk.Button):
    def _update(self, **kwargs):
        if "image" in kwargs:
            self.image = kwargs["image"]
            self.config(image=kwargs["image"])
            
        if "command" in kwargs:
            #self.bind("<Button-1>", lambda event: kwargs["command"]())
            self.config(command=kwargs["command"])
            
    def __init__(self, master=None, **kwargs):
        super().__init__(master, style="QuickAccessToolbarButton.TButton")
        
        self._update(**kwargs)

    def configure(self, cnf=None, **kwargs):
        if cnf is None: cnf = {}
        kwargs.update(cnf)
        
        self._update(**kwargs)
        
        return super().configure(cnf)

class MenuBar(Menu):
    globalVars = None
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        hm = MenuBar.globalVars.historyManager
        
        def updateEditMenu(cmd = None):
            if len(hm.undoStack) == 0: editMenu.entryconfig("Undo", state="disabled")
            else: editMenu.entryconfig("Undo", state="normal")
            
            if len(hm.redoStack) == 0: editMenu.entryconfig("Redo", state="disabled")
            else: editMenu.entryconfig("Redo", state="normal")
        
        # file
        fileMenu = Menu(self, tearoff=0)
        # fileMenu.add_command(label="New", accelerator="Ctrl+Z")
        # fileMenu.add_command(label="Open...", accelerator="Ctrl+Y")
        # fileMenu.add_command(label="Save", accelerator="Ctrl+S")
        # fileMenu.add_command(label="Save As...", accelerator="Ctrl+Shift+S")
        
        # fileMenu.add_separator()
        
        # # print
        # fileMenu.add_command(label="Print", accelerator="Ctrl+P")
        
        # fileMenu.add_separator()
        
        # export
        exportMenu = Menu(fileMenu, tearoff=0)
        exportMenu.add_command(label="Image", command=lambda: ExportAsImageMenu(MenuBar.globalVars.root))
        exportMenu.add_command(label="PDF", command=lambda: ExportAsPDF(MenuBar.globalVars.root))
        
        fileMenu.add_cascade(label="Export As...", menu=exportMenu)
        
        # edit
        editMenu = Menu(self, tearoff=0)
        editMenu.add_command(label="Undo", accelerator="Ctrl+Z", command=hm.undo)
        editMenu.add_command(label="Redo", accelerator="Ctrl+Y", command=hm.redo)

        hm.onUndo.append(updateEditMenu)
        hm.onRedo.append(updateEditMenu)
        hm.onDo.append(updateEditMenu)
        
        updateEditMenu()
        
        # view
        viewMenu = Menu(self, tearoff=0)
        viewMenu.add_checkbutton(label="Properties", variable=MenuBar.globalVars.showPropertyMenu)

        # unit
        unitMenu = Menu(self, tearoff=0)
        unitMenu.add_radiobutton(label="Inches (in)", value="in", variable=MenuBar.globalVars.unit)
        unitMenu.add_radiobutton(label="Centimeters (cm)", value="cm", variable=MenuBar.globalVars.unit)
        unitMenu.add_radiobutton(label="Millimeters (mm)", value="mm", variable=MenuBar.globalVars.unit)
        
        # help
        helpMenu = Menu(self, tearoff=0)
        helpMenu.add_command(label="Help", command=lambda: webbrowser.open_new_tab("https://sites.google.com/view/markbigmuscle2/home"))

        self.add_cascade(label="File", menu=fileMenu)
        self.add_cascade(label="Edit", menu=editMenu)
        self.add_cascade(label="View", menu=viewMenu)
        self.add_cascade(label="Units", menu=unitMenu)
        self.add_cascade(label="Help", menu=helpMenu)

class PropertyMenu(Frame):
    globalVars = None
    
    def __init__(self, master=None, **kwargs):
        super().__init__(master, width=300, bd=2, relief=RIDGE, **kwargs)
        self.selection = []
        self.tempSelection = []
        self.lastSelection = []
        
        self._topLabel = Label(self, text="Properties", bd=2, relief=RIDGE)
        self._topLabel.pack(fill="x", ipadx=2, ipady=2)
        
        self._content = Frame(self, bg="white")
        self._content.pack(fill=BOTH, expand=True)
        
        self.selecting = BooleanVar(value=False)
        
        self._propertyList = None
        self.inputs = {}
        
    def clearSelection(self):
        combinedSelections = set(tuple(self.selection))
        combinedSelections.update(self.lastSelection)
        
        for drawing in combinedSelections:
            drawing.selected.set(False)
            
        self.selection = []
        self.lastSelection = []
        
        self.updateSelection()
        
    def _convertPx(self, value=0, unit="px"):
        globalVars = PropertyMenu.globalVars
        ppi = globalVars.ppi.get()
        
        if unit == "in":
            return float(Decimal(str(value)) / Decimal(str(ppi)))
        elif unit == "cm":
            return float(Decimal(str(value)) / (Decimal(str(ppi)) / Decimal(str(2.54))))
        elif unit == "mm":
            return float(Decimal(str(value)) / (Decimal(str(ppi)) / Decimal(str(25.4))))
        return value
        
    def _convertToAbsoluteSize(self, value=0, unit="px"): 
        globalVars = Ribbon.globalVars
        ppi = globalVars.ppi.get()
        
        if unit == "in":
            return float(Decimal(str(value)) * Decimal(str(ppi)))
        elif unit == "cm":
            return float(Decimal(str(value)) * Decimal(str(ppi)) / Decimal(str(2.54)))
        elif unit == "mm":
            return float(Decimal(str(value)) * Decimal(str(ppi)) / Decimal(str(25.4)))
        return value
        
    def finishSelection(self):
        self.selecting.set(False)
        
        self.lastSelection = self.selection.copy()
        
    def loadProperties(self, *drawings):
        globalVars = PropertyMenu.globalVars
        
        if self._propertyList is not None: 
            self._propertyList.destroy()
        self._propertyList = Frame(self._content)

        self.inputs.clear()
        
        # 1. Group properties by category and name across all drawings
        properties = {}
        for drawing in drawings:
            for category in drawing.properties.get():
                if category not in properties: 
                    properties[category] = {}
                
                group = properties[category]
                groupProperties = drawing.properties.get(category)
                
                for prop in groupProperties:
                    if prop.name not in group: group[prop.name] = []
                    group[prop.name].append(prop)
        
        # 2. Build UI elements per category
        for category, groupProperties in properties.items():
            categorySection = Frame(self._propertyList)
            categorySection.pack(fill="x", expand=True)
            
            categoryLabel = Label(categorySection, text=category, bd=2, relief=RIDGE, anchor="w", justify="left")
            categoryLabel.pack(fill="x")
            
            categoryContent = Frame(categorySection, bg="white")
            categoryContent.pack(fill="x", expand=True)
            
            for propName, propDataList in groupProperties.items():
                Prop = propDataList[0]
                variableList = [p.variable for p in propDataList]
                valueList = [p.value for p in propDataList]
                
                # Determine entry type
                if isinstance(Prop.variable, BooleanVar):
                    continue  # Handled separately if needed
                    
                entryType = "Text"
                if isinstance(Prop.variable, DoubleVar): 
                    entryType = "Double"
                elif isinstance(Prop.variable, IntVar): 
                    entryType = "Integer"
                    
                labelConfig = {
                    "bg": "white", 
                    "anchor": "w", 
                    "justify": "left", 
                    "bd": 2, 
                    "relief": RIDGE
                }
                
                # Instantiate appropriate widget
                if Prop.useOptions:
                    dropdownConfig = {"borderwidth": 2, "relief": RIDGE}
                    widget = LabeledDropdown(
                        categoryContent, 
                        label=Prop.name, 
                        options=Prop.options, 
                        labelConfig=labelConfig, 
                        dropdownConfig=dropdownConfig, 
                        variables=variableList, 
                        values=valueList, 
                        readOnly=Prop.readOnly
                    )
                else:
                    entryConfig = {"bd": 2, "relief": RIDGE}
                    widget = LabeledEntry(
                        categoryContent, 
                        label=Prop.name, 
                        useUnit=Prop.useUnit, 
                        labelConfig=labelConfig, 
                        entryConfig=entryConfig, 
                        variables=variableList, 
                        values=valueList, 
                        readOnly=Prop.readOnly
                    )
                    
                widget.grid_columnconfigure(0, weight=1, uniform="_")
                widget.grid_columnconfigure(1, weight=1, uniform="_")
                
                widget.pack(fill="x")
                
                # 3. Unified change handler with properly bound closure variables
                values = {}
                lastValues = {}
                lastInputValue = widget.get()
                
                def make_on_change(p_prop, p_widget, p_prop_data_list, p_values, p_last_values, p_last_input_value):
                    def onChange(returnPressed):
                        p_values.clear()
                        inputValue = p_widget.get()
                        
                        for prop in p_prop_data_list:
                            for f in prop.object.properties.onChange: 
                                f(prop, inputValue)
                                
                            prop.value = prop.variable.get() if prop.variable else inputValue
                            p_values[prop] = prop.value
                            
                        if returnPressed and p_last_values != p_values:
                            print("add to history")
                            PropertyMenu.globalVars.historyManager.do(PropertyChangedCommand(
                                name=p_prop.name,
                                properties=p_prop_data_list, 
                                values=dict(p_values), 
                                lastValues=dict(p_last_values),
                                inputValue=inputValue,
                                lastInputValue=p_last_input_value
                            ))
                            
                        for prop in p_prop_data_list:
                            prop.lastValue = prop.value
                            
                        p_last_values.clear()
                        p_last_values.update(p_values)
                        
                    return onChange

                bound_onChange = make_on_change(Prop, widget, propDataList, values, lastValues, lastInputValue)
                
                # Initialize state and register callback
                bound_onChange(False)
                widget.onChange.append(bound_onChange)
                self.inputs[Prop.name] = widget
           
        self._propertyList.pack(anchor="n", fill="x")
        
    def startSelection(self):
        self.selecting.set(True)
        
    def updateProperty(self, name, value):
        propertyInput = self.inputs[name] if name in self.inputs else None
        
        if not propertyInput: return
        
        propertyInput.set(value)
        
    def updateSelection(self, *drawings, **kwargs):
        from geometry import Drawing, Dimension
        defaultKwArgs = {
            "ctrlKeyPressed": False,
            "reloadSameSelection": False,
        }
        
        defaultKwArgs.update(kwargs)
        
        self.selection = [drawing for drawing in drawings if drawing is not None]
        
        if not self.selecting.get(): return
        
        if defaultKwArgs["ctrlKeyPressed"]:
            temp = []
            
            for drawing in self.selection:
                if isinstance(drawing, Drawing):
                    if drawing not in self.lastSelection:
                        temp.append(drawing)
                    drawing.selected.set(drawing not in self.lastSelection)

            for drawing in self.lastSelection:
                if isinstance(drawing, Drawing):
                    if drawing not in self.selection:
                        drawing.selected.set(True)
                        temp.append(drawing)
                    
            self.selection = temp
        else:
            for drawing in self.selection:
                if isinstance(drawing, Drawing):
                    drawing.selected.set(True)
                
        for drawing in self.tempSelection:
            if isinstance(drawing, Drawing):
                if drawing not in self.selection:
                    drawing.selected.set(False)
        
        if len(self.selection) == 0:
            self._topLabel.config(text="Properties")
        elif len(self.selection) == 1:
            self._topLabel.config(text=f"Properties - {self.selection[0].type}")
        elif len(self.selection) > 1:
            self._topLabel.config(text=f"Properties - {len(self.selection)} items selected")

        if defaultKwArgs["reloadSameSelection"]:
            self.loadProperties(*self.selection)
        elif self.tempSelection != self.selection:
            self.loadProperties(*self.selection)
            
        self.tempSelection = self.selection
        
class Ribbon(Frame):
    canvas = None
    globalVars = None
    propertyMenu = None
    
    def __init__(self, master=None, **kwargs):
        defaultKwArgs = { "bg": "white" }
        defaultKwArgs.update(kwargs)
        
        hm = MenuBar.globalVars.historyManager
        
        super().__init__(master, **defaultKwArgs)
        self.tools = {
            "Arc": ct.ArcTool(), 
            "Circle": ct.CircleTool(["Center, Point", "2 Points"]), 
            "Dimension": ct.DimensionTool(["Linear", "Aligned", "Radial", "Diametric"]), 
            "Erase": ct.EraseTool(), 
            "Line": ct.LineTool(["2 Points", "2 Points with Center"]), 
            "Pan": ct.PanTool(), 
            "Rectangle": ct.RectangleTool(), 
            "Select": ct.SelectTool(), 
            "Text": ct.TextTool()
        }
        self.__toolSettings = None
        
        def handleTool(tool="Select"):
            globalVars = Ribbon.globalVars
            if globalVars.toolObject: globalVars.toolObject.finish()
            globalVars.tool.set(tool)
            globalVars.toolObject = self.tools[tool]
            globalVars.toolObject.start()
            
            if globalVars.tool.get() != globalVars.lastTool.get():
                if self.__toolSettings: self.__toolSettings.destroy()
                
                self.__toolSettings = ToolSettings(self.__toolSettingsFrame, tool, self.tools[tool], bg=defaultKwArgs["bg"])
                self.__toolSettings.pack(anchor="w", fill="x", expand=True)
            
            globalVars.lastTool.set(tool)
            
        for i in self.tools:
            self.tools[i].mode.trace_add("write", lambda a, b, c, i=i: handleTool(i))
            
        self.grid_columnconfigure(0, weight=1)
        
        # toolbar row 0
        quickAccessTb = Frame(self, bg=defaultKwArgs["bg"])
        quickAccessTb.grid(row=0, column=0, columnspan=6, sticky="we")
        
        # QuickAccessToolbarButton(quickAccessTb, image=PhotoImage(file=SCRIPT_DIR / "images" / "new-file-icon.png")).pack(side=LEFT)
        # QuickAccessToolbarButton(quickAccessTb, image=PhotoImage(file=SCRIPT_DIR / "images" / "open-icon.png")).pack(side=LEFT)
        # QuickAccessToolbarButton(quickAccessTb, image=PhotoImage(file=SCRIPT_DIR / "images" / "save-icon.png")).pack(side=LEFT)
        
        # ttk.Separator(quickAccessTb, style="Line.TSeparator", orient="vertical").pack(side=LEFT, fill="y", padx=2)
        
        # QuickAccessToolbarButton(quickAccessTb, image=PhotoImage(file=SCRIPT_DIR / "images" / "print-icon.png")).pack(side=LEFT)
        
        # ttk.Separator(quickAccessTb, style="Line.TSeparator", orient="vertical").pack(side=LEFT, fill="y", padx=2)
        
        exportBtn = QuickAccessToolbarButton(quickAccessTb, image=PhotoImage(file=SCRIPT_DIR / "images" / "export-icon.png"))
        
        ttk.Separator(quickAccessTb, style="Line.TSeparator", orient="vertical").pack(side=LEFT, fill="y", padx=2)
        
        undoBtn = QuickAccessToolbarButton(quickAccessTb, image=PhotoImage(file=SCRIPT_DIR / "images" / "undo-icon.png"))
        redoBtn = QuickAccessToolbarButton(quickAccessTb, image=PhotoImage(file=SCRIPT_DIR / "images" / "redo-icon.png"))

        def update(cmd = None):
            if len(hm.undoStack) == 0: undoBtn.state(["disabled"])
            else: undoBtn.state(["!disabled"])
            
            if len(hm.redoStack) == 0: redoBtn.state(["disabled"])
            else: redoBtn.state(["!disabled"])
        
        def undo():
            hm.undo()
            update()
            
        def redo():
            hm.redo()
            update()
            
        def export(event):
            exportMenu = Menu(Ribbon.globalVars.root, tearoff=0)
            exportMenu.add_command(label="Image", command=lambda: ExportAsImageMenu(MenuBar.globalVars.root))
            exportMenu.add_command(label="PDF", command=lambda: ExportAsPDF(MenuBar.globalVars.root))
            
            exportMenu.tk_popup(event.x_root, event.y_root)

        exportBtn.bind("<Button-1>", export)
        exportBtn.pack(side=LEFT)
        
        undoBtn.config(command=undo)
        undoBtn.pack(side=LEFT)
        
        redoBtn.config(command=redo)
        redoBtn.pack(side=LEFT)
        
        hm.onUndo.append(update)
        hm.onRedo.append(update)
        hm.onDo.append(update)
        
        update()
        
        ttk.Separator(self, style="Line.TSeparator").grid(row=1, column=0, sticky="we")
        
        # toolbar row 1
        tbr1 = Frame(self, bg=defaultKwArgs["bg"])
        tbr1.grid(row=2, column=0, sticky="we")
        
        # toolbar group 1
        tbg1 = Frame(tbr1, bg=defaultKwArgs["bg"])
        tbg1.grid(row=0, column=0, padx=4, pady=4, sticky="n")

        tbg1Buttons = Frame(tbg1, bg=defaultKwArgs["bg"])
        tbg1Buttons.pack()
        
        dimMenu = Menu(Ribbon.globalVars.root, tearoff=0)
        dimMenu.add_radiobutton(label="Linear", value=0, variable=self.tools["Dimension"].mode)
        dimMenu.add_radiobutton(label="Aligned", value=1, variable=self.tools["Dimension"].mode)
        dimMenu.add_radiobutton(label="Radial", value=2, variable=self.tools["Dimension"].mode)
        dimMenu.add_radiobutton(label="Diametric", value=3, variable=self.tools["Dimension"].mode)
        
        # buttons
        toolButtons1 = [
            ToolButton(tbg1Buttons, image=PhotoImage(file=SCRIPT_DIR / "images" / "select-icon-32.png"), label="Select", command=lambda: handleTool("Select")),
            ToolButton(tbg1Buttons, image=PhotoImage(file=SCRIPT_DIR / "images" / "pan-icon-32.png"), label="Pan", command=lambda: handleTool("Pan")),
            ToolButton(tbg1Buttons, image=PhotoImage(file=SCRIPT_DIR / "images" / "text-icon-32.png"), label="Text", command=lambda: handleTool("Text")),
            ToolButton(tbg1Buttons, image=PhotoImage(file=SCRIPT_DIR / "images" / "dimension-icon-32.png"), label="Dimension", command=lambda: handleTool("Dimension"), menu=dimMenu),
            ToolButton(tbg1Buttons, image=PhotoImage(file=SCRIPT_DIR / "images" / "eraser-icon-32.png"), label="Erase", command=lambda: handleTool("Erase"))
        ]
        
        for tb in toolButtons1: tb.pack(side=LEFT, fill="y")
        
        Label(tbr1, bg=defaultKwArgs["bg"], text="Tools").grid(row=1, column=0)
        
        ttk.Separator(tbr1, orient="vertical").grid(row=0, column=1, rowspan=2, sticky="ns")
        
        # toolbar group 2
        
        tbg2 = Frame(tbr1, bg=defaultKwArgs["bg"])
        tbg2.grid(row=0, column=2, padx=4, pady=4, sticky="n")

        tbg2Buttons = Frame(tbg2, bg=defaultKwArgs["bg"])
        tbg2Buttons.pack()
        
        lineMenu = Menu(Ribbon.globalVars.root, tearoff=0)
        lineMenu.add_radiobutton(label="2 Points", value=0, variable=self.tools["Line"].mode)
        lineMenu.add_radiobutton(label="2 Points with Center", value=1, variable=self.tools["Line"].mode)
        
        circleMenu = Menu(Ribbon.globalVars.root, tearoff=0)
        circleMenu.add_radiobutton(label="Center, Point", value=0, variable=self.tools["Circle"].mode)
        circleMenu.add_radiobutton(label="2 Points", value=1, variable=self.tools["Circle"].mode)
        
        toolButtons2 = [
            ToolButton(tbg2Buttons, image=PhotoImage(file=SCRIPT_DIR / "images" / "line-icon-32.png"), label="Line", command=lambda: handleTool("Line"), menu=lineMenu),
            ToolButton(tbg2Buttons, image=PhotoImage(file=SCRIPT_DIR / "images" / "arc-icon-32.png"), label="Arc", command=lambda: handleTool("Arc")),
            ToolButton(tbg2Buttons, image=PhotoImage(file=SCRIPT_DIR / "images" / "circle-icon-32.png"), label="Circle", command=lambda: handleTool("Circle"), menu=circleMenu),
            ToolButton(tbg2Buttons, image=PhotoImage(file=SCRIPT_DIR / "images" / "rectangle-icon-32.png"), label="Rectangle", command=lambda: handleTool("Rectangle")),
        ]
        
        Label(tbr1, bg=defaultKwArgs["bg"], text="Geometry").grid(row=1, column=2)
        
        for tb in toolButtons2: tb.pack(side=LEFT, fill="y")
        
        ttk.Separator(tbr1, orient="vertical").grid(row=0, column=3, rowspan=2, sticky="ns")
        
        # toolbar group 3
        
        tbg3 = Frame(tbr1, bg=defaultKwArgs["bg"])
        tbg3.grid(row=0, column=4, padx=4, pady=4, sticky="n")
        
        tbg3Content = Frame(tbg3, bg=defaultKwArgs["bg"])
        tbg3Content.pack()
        
        gridSizeFrame = Frame(tbg3Content, bg=defaultKwArgs["bg"])
        gridSizeFrame.pack()
        
        Label(gridSizeFrame, bg=defaultKwArgs["bg"], text="Size:").pack(side=LEFT)
        
        gridSize = Spinbox(gridSizeFrame, width=6, justify="right", from_=0, to=200, increment=.1)
        gridSize.pack(side=LEFT)
        gridSize.bind("<Return>", lambda event: Ribbon.globalVars.root.focus_set())
        
        unit = Label(gridSizeFrame, bg=defaultKwArgs["bg"])
        unit.pack(side=LEFT)
        
        snapToGrid = Checkbutton(tbg3Content, bg=defaultKwArgs["bg"], text="Snap to Grid")
        snapToGrid.pack(anchor="w")
        
        showGrid = Checkbutton(tbg3Content, bg=defaultKwArgs["bg"], text="Show Grid")
        showGrid.pack(anchor="w")
        
        Label(tbr1, bg=defaultKwArgs["bg"], text="Grid").grid(row=1, column=4)
        
        ttk.Separator(tbr1, orient="vertical").grid(row=0, column=5, rowspan=2, sticky="ns")
        
        # toolbar group 4
        
        tbg4 = Frame(tbr1, bg=defaultKwArgs["bg"])
        tbg4.grid(row=0, column=6, padx=4, pady=4, sticky="n")
        
        tbg4Content = Frame(tbg4, bg=defaultKwArgs["bg"])
        tbg4Content.pack()
        
        rotationFrame = Frame(tbg4Content, bg=defaultKwArgs["bg"])
        rotationFrame.pack()
        
        Label(rotationFrame, bg=defaultKwArgs["bg"], text="Angle:").pack(side=LEFT)
        
        angleIncrement = Spinbox(rotationFrame, width=6, justify="right", from_=0, to=180, increment=5)
        angleIncrement.pack(side=LEFT)
        angleIncrement.bind("<Return>", lambda event: Ribbon.globalVars.root.focus_set())
        
        unit2 = Label(rotationFrame, bg=defaultKwArgs["bg"], text="degrees")
        unit2.pack(side=LEFT)
        
        snapToRotate = Checkbutton(tbg4Content, bg=defaultKwArgs["bg"], text="Snap to Rotate")
        snapToRotate.pack(anchor="w")
        
        Label(tbr1, bg=defaultKwArgs["bg"], text="Rotation").grid(row=1, column=6)
        
        ttk.Separator(tbr1, orient="vertical").grid(row=0, column=7, rowspan=2, sticky="ns")
        
        # toolbar group 5
        
        tbg5 = Frame(tbr1, bg=defaultKwArgs["bg"])
        tbg5.grid(row=0, column=8, padx=4, pady=4, sticky="n")
        
        tbg5Content = Frame(tbg5, bg=defaultKwArgs["bg"])
        tbg5Content.pack()
        
        Checkbutton(tbg5Content, bg=defaultKwArgs["bg"], text="Show Center", variable=self.globalVars.showCenter).pack(anchor="w")
        Checkbutton(tbg5Content, bg=defaultKwArgs["bg"], text="Show Other", variable=self.globalVars.showOtherPoints).pack(anchor="w")
        Checkbutton(tbg5Content, bg=defaultKwArgs["bg"], text="Snap to Point", variable=self.globalVars.snapToPoint).pack(anchor="w")
        
        Label(tbr1, bg=defaultKwArgs["bg"], text="Points").grid(row=1, column=8)
        
        ttk.Separator(self, style="Line.TSeparator").grid(row=3, column=0, sticky="we")
        
        # toolbar row 2
        toolSettingsFrame = Frame(self, bg=defaultKwArgs["bg"])
        toolSettingsFrame.grid(row=4, column=0, sticky="we")
        
        self.__unit = unit
        self.__gridSize = gridSize
        self.__snapToGrid = snapToGrid
        self.__showGrid = showGrid
        
        self.__angleIncrement = angleIncrement
        self.__snapToRotate = snapToRotate
        
        self.__toolSettingsFrame = toolSettingsFrame
        
        def zoomChanged(a, b, c):
            globalVars = Ribbon.globalVars
            tool = Ribbon.globalVars.tool.get()
            
            if tool == "Line": globalVars.toolObject.createPointPosition()
            elif tool == "Arc": globalVars.toolObject.createPointPosition("red")
            
        def dimensionSelectionTypeChanged(a, b, c):
            globalVars = Ribbon.globalVars
            tool = globalVars.tool.get()
            
            if tool == "Dimension":
                globalVars.toolObject.finish()
                globalVars.toolObject.start()
        
        Ribbon.globalVars.zoom.trace_add("write", zoomChanged)
        Ribbon.globalVars.dimensionSelectionType.trace_add("write", dimensionSelectionTypeChanged)
    
    def finishTool(self, tool):
        globalVars = Ribbon.globalVars
        if globalVars.toolObject: globalVars.toolObject.finish()
    
    def startTool(self, tool):
        globalVars = Ribbon.globalVars
        if globalVars.toolObject: globalVars.toolObject.start()
        
    def toolActivated(self, event):
        globalVars = Ribbon.globalVars
        if globalVars.toolObject: globalVars.toolObject.toolActivated(event)
        
    def toolBtn1Down(self, event, ctrlPressed=False):
        globalVars = Ribbon.globalVars
        if globalVars.toolObject: globalVars.toolObject.toolBtn1Down(event, ctrlPressed)
        
    def toolBtn1Motion(self, event, ctrlPressed=False):
        globalVars = Ribbon.globalVars
        if globalVars.toolObject: globalVars.toolObject.toolBtn1Motion(event, ctrlPressed)
        
    def toolMotion(self, event, ctrlPressed=False):
        globalVars = Ribbon.globalVars
        if globalVars.toolObject: globalVars.toolObject.toolMotion(event, ctrlPressed)
        
    def bindGlobalVariables(self, globalVars):  
        self.__unit.config(textvariable=globalVars.unit)
        self.__gridSize.config(textvariable=globalVars.gridSize)
        
        self.__angleIncrement.config(textvariable=globalVars.angleIncrement)
        self.__snapToRotate.config(variable=globalVars.snapToRotate)
        
        self.__snapToGrid.config(variable=globalVars.snapToGrid)
        self.__showGrid.config(variable=globalVars.showGrid)

class ToolSettings(Frame):
    globalVars = None
    
    def __init__(self, master=None, tool="", toolObject=None, **kwargs):
        super().__init__(master, **kwargs)
        self.tool = tool
        self.toolObject = toolObject
        
        # for generic tools
        Label(self, text="Mode:", bg="white").pack(side=LEFT)
        Label(self, textvariable=toolObject.modeName, bg="white").pack(side=LEFT)
        
        ttk.Separator(self, style="Line.TSeparator", orient="vertical").pack(side=LEFT, fill="y", padx=2)
        
        if tool == "Dimension":
            Label(self, text="Selection Type:", bg="white").pack(side=LEFT)
            dimensionSelectionType = ttk.Combobox(self, textvariable=ToolSettings.globalVars.dimensionSelectionType, values=["Drawing", "Point"], state="readonly")
            dimensionSelectionType.pack(side=LEFT)
            
            ttk.Separator(self, style="Line.TSeparator", orient="vertical").pack(side=LEFT, fill="y", padx=2)
            
            def openPopup():
                DimensionStyleSettings(ToolSettings.globalVars.root)
                    
            Button(self, text="Edit Style", command=openPopup).pack(side=LEFT)

class StatusBar(Frame):
    globalVars = None
    
    def __init__(self, master=None, **kwargs):
        globalVars = StatusBar.globalVars
        
        viewOffset = globalVars.viewOffset
        viewOffset.mapForCanvas()
        
        canvasCursorPosition = globalVars.canvasCursorPosition
        
        super().__init__(master, **kwargs)

        toolGroup = Frame(self)
        toolGroup.pack(side=LEFT, padx=8)
        
        toolGroupLabel1 = Label(toolGroup, text="Tool:")
        toolGroupLabel1.pack(side=LEFT)
        
        toolGroupLabel2 = Label(toolGroup, textvariable=globalVars.tool)
        toolGroupLabel2.pack(side=LEFT)
        
        ttk.Separator(self, orient="vertical").pack(side=LEFT, fill="y")
        
        coordsGroup = Frame(self)
        coordsGroup.pack(side=LEFT, padx=8)
        
        viewOffsetLabel1 = Label(coordsGroup, text="View Offset:")
        viewOffsetLabel1.pack(side=LEFT)
        
        viewOffsetLabel2 = Label(coordsGroup, textvariable=viewOffset.StringVar)
        viewOffsetLabel2.pack(side=LEFT)
        
        ttk.Separator(self, orient="vertical").pack(side=LEFT, fill="y")
        
        canvasCursorPosGroup = Frame(self)
        canvasCursorPosGroup.pack(side=LEFT, padx=8)
        
        canvasCursorPosLabel1 = Label(canvasCursorPosGroup, text="Cursor Position:")
        canvasCursorPosLabel1.pack(side=LEFT)
        
        canvasCursorPosLabel2 = Label(canvasCursorPosGroup, textvariable=canvasCursorPosition.StringVar)
        canvasCursorPosLabel2.pack(side=LEFT)
        
        ttk.Separator(self, orient="vertical").pack(side=LEFT, fill="y")
        
        zoomGroup = Frame(self)
        zoomGroup.pack(side=LEFT, padx=8)
        
        zoomLabel1 = Label(zoomGroup, text="Zoom:")
        zoomLabel1.pack(side=LEFT)
        
        lastValue = globalVars.zoom.get()

        zoomEntry = Entry(zoomGroup, justify="right", width=6)
        
        zoomEntry.insert(0, lastValue)
        zoomEntry.pack(side=LEFT)
        
        def zoomChanged(event):
            Ribbon.globalVars.root.focus_set()
            nonlocal lastValue
            with suppress(Exception):
                float(zoomEntry.get())
                globalVars.zoom.set(zoomEntry.get())
            
            updateZoomEntry()
            
        def updateZoomEntry(*args):
            from geometry import Drawing, Dimension
            
            lastValue = globalVars.zoom.get()
            
            zoomEntry.delete(0, END)
            zoomEntry.insert(0, lastValue)
            
            Drawing.redrawAll()
            Dimension.redrawAll()
            
        zoomEntry.bind("<Return>", zoomChanged)
        
        globalVars.zoom.trace_add("write", updateZoomEntry)
        
        zoomLabel2 = Label(zoomGroup, text="%")
        zoomLabel2.pack(side=LEFT)
