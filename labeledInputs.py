from tkinter import *
from tkinter import ttk

from contextlib import suppress
from conversions import Conversions

convertPx = Conversions.convertPx
convertToAbsoluteSize = Conversions.convertToAbsoluteSize

import re

class LabeledInput(Frame):
    globalVars = None
    
    def __init__(self, master=None, **kwargs):
        defaultKwArgs = {
            "frameConfig": {},
            "label": "Label",
            "labelConfig": { "anchor": "w", "justify": "left" },
            "readOnly": False,
            "type": "Text",
            "variables": [],
            "values": [""],
            "windowFocus": LabeledInput.globalVars.root
        }
        
        defaultKwArgs.update(kwargs)
        
        super().__init__(master, **defaultKwArgs["frameConfig"])
        
        for key in defaultKwArgs:
            setattr(self, key, defaultKwArgs[key])

        self._configure = None
        
        # self.grid_columnconfigure(0, weight=1, uniform="_")
        # self.grid_columnconfigure(1, weight=1, uniform="_")
            
        labelConfig = self.labelConfig
            
        labelWidget = Label(self, text=self.label, **labelConfig)
        labelWidget.grid(row=0, column=0, sticky="nsew")

    def configure(self, cnf=None, **kwargs):
        if cnf is None: cnf = {}
        kwargs.update(cnf)
        
        if self._configure: self._configure(**kwargs)
        
    def _fixedValueAndUnitFormat(self, text, resultingUnit):
        text = str(text)
        
        matchA = re.search(r"^([+-]?\d+(?:\.\d+)?)$", text.strip()) # value only
        matchB = re.search(r"^([+-]?\d+(?:\.\d+)?)\s?(\w+)$", text.strip()) # value and unit
        matchC = re.search(r"^([+-]?(?:\.\d+)?)$", text.strip()) # value without whole number
        matchD = re.search(r"^([+-]?(?:\.\d+)?)\s?(\w+)$", text.strip()) # value without whole number and unit
        
        result = ""
        
        if matchA:
            value = float(matchA.group(1))
        elif matchB:
            unit = matchB.group(2)
            value = convertPx(convertToAbsoluteSize(matchB.group(1), unit), resultingUnit)
        elif matchC:
            value = float(matchC.group(1))
        elif matchD:
            unit = matchD.group(2)
            value = convertPx(convertToAbsoluteSize(matchD.group(1), unit), resultingUnit)
            
        result = f"{value} {resultingUnit}"
        
        return result
        
    def set(self, value):
        if isinstance(self, LabeledEntry):
            entry = self._input
            entry.delete(0, END)

            Type = self.type
            unitVar = self.unitVar
            useUnit = self.useUnit
            
            if useUnit:
                if value != "multiple": entry.insert(0, self._fixedValueAndUnitFormat(value, unitVar.get()))
            else:
                entry.insert(0, value)
        elif isinstance(self, LabeledDropdown):
            dropdown = self._input
            dropdown.set(value)
            # self.variable.set(dropdown.get())
            
class LabeledEntry(LabeledInput):
    def __init__(self, master=None, **kwargs):
        globalVars = LabeledInput.globalVars

        defaultKwArgs = {
            "entryConfig": {},
            "unitVar": globalVars.unit,
            "useUnit": False,
        }
        
        defaultKwArgs.update(kwargs)
        
        super().__init__(master, **defaultKwArgs)
        self._lastUnit = "in"
        self._input = None
        self.onChange = []
        
        unitVar = self.unitVar
        useUnit = self.useUnit
        variables = self.variables
        
        initialValue = self.values[0] if len(self.values) > 0 else None
        
        multipleValues = initialValue and self.values.count(initialValue) != len(self.values)
        returnPressed = False
        unitChanged = False

        if self.type == "Text":
            self.variable = StringVar(value=initialValue if initialValue else "")
        elif self.type == "Integer":
            self.variable = IntVar(value=initialValue if initialValue else 0)
        elif self.type == "Double":
            self.variable = DoubleVar(value=initialValue if initialValue else 0)
        
        def onReturn(event):
            nonlocal returnPressed
            returnPressed = True
                                
            self.windowFocus.focus_set()
            
            unitVarValue = unitVar.get()
            
            entryText = entry.get()
            value = entryText
            
            if useUnit:
                matchA = re.search(r"^([+-]?\d+(?:\.\d+)?)$", entryText.strip()) # value only
                matchB = re.search(r"^([+-]?\d+(?:\.\d+)?)\s?(\w+)$", entryText.strip()) # value and unit
                matchC = re.search(r"^([+-]?(?:\.\d+)?)$", entryText.strip()) # value without whole number
                matchD = re.search(r"^([+-]?(?:\.\d+)?)\s?(\w+)$", entryText.strip()) # value without whole number and unit
                
                if matchA:
                    value = float(matchA.group(1))
                elif matchB:
                    unit = matchB.group(2)
                    value = convertPx(convertToAbsoluteSize(matchB.group(1), unit), unitVarValue)
                elif matchC:
                    value = float(matchC.group(1))
                elif matchD:
                    unit = matchD.group(2)
                    value = convertPx(convertToAbsoluteSize(matchD.group(1), unit), unitVarValue)
                    
            with suppress(Exception):       
                if isinstance(self.variable, DoubleVar):
                    self.variable.set(float(value))
                elif isinstance(self.variable, IntVar):
                    self.variable.set(int(value))
                else:
                    self.variable.set(value)
            
            entry.delete(0, END)
            if useUnit: entry.insert(0, self._fixedValueAndUnitFormat(self.variable.get(), unitVarValue))
            else: entry.insert(0, self.variable.get())
            
            returnPressed = False
            
        def variableChanged(*args):
            # print(self.variable.get())
            
            for variable in variables:
                if variable:
                    variable.set(self.variable.get())
                
            if not unitChanged: 
                for f in self.onChange: f(returnPressed)
                    
            if not returnPressed:
                unitVarValue = unitVar.get()
                
                with suppress(Exception):
                    entry.delete(0, END)
                    
                    if useUnit: entry.insert(0, f"{self.variable.get()} {unitVarValue}")
                    else: entry.insert(0, self.variable.get())
                    
        def onUnitChange(*args):
            nonlocal unitChanged
            unitChanged = True
            
            unitVarValue = unitVar.get()
            
            value = convertPx(convertToAbsoluteSize(self.variable.get(), self._lastUnit), unitVarValue)
            
            with suppress(Exception):
                if isinstance(self.variable, DoubleVar):
                    self.variable.set(float(value))
                elif isinstance(self.variable, IntVar):
                    self.variable.set(int(value))
                else:
                    self.variable.set(value)
                    
                entry.delete(0, END)
                
                if useUnit: entry.insert(0, f"{value} {unitVarValue}")
                else: entry.insert(0, value)
                    
            self._lastUnit = unitVar.get()
            
            unitChanged = False
        
        entryConfig = self.entryConfig
        
        entry = Entry(self, **entryConfig)
        entry.grid(row=0, column=1, sticky="nsew")
        
        entry.bind("<Return>", onReturn)
        
        self.variable.trace_add("write", variableChanged)
        unitVar.trace_add("write", onUnitChange)
        
        currentValue = self.variable.get()
        
        if multipleValues:
            entry.insert(0, "multiple")
        else:
            if useUnit: 
                unitVarValue = unitVar.get()
                entry.insert(0, f"{currentValue} {unitVarValue}")
            else: entry.insert(0, currentValue)

        if self.readOnly: entry.configure(state="readonly")
        
        self._input = entry
    
    def _configure(self, **kwargs):
        pass
        
    def get(self):
        return self._input.get()

class LabeledDropdown(LabeledInput):
    globalVars = None
    
    def get(self):
        return self._input.get()
    
    def __init__(self, master=None, **kwargs):
        globalVars = LabeledEntry.globalVars
        
        defaultKwArgs = {
            "dropdownConfig": {},
            "type": "Text"
        }
        
        defaultKwArgs.update(kwargs)
        
        super().__init__(master, **defaultKwArgs)
        self._input = None
        self.onChange = []
        
        initialValue = self.values[0] if len(self.values) > 0 else None
        
        multipleValues = initialValue and self.values.count(initialValue) != len(self.values)
        returnPressed = False
        modifyVariables = False
        
        self.variable = StringVar(value=initialValue if initialValue else "")
        
        def comboboxSelected(event):
            nonlocal returnPressed
            returnPressed = True
            
            self.variable.set(dropdown.get())
            
            returnPressed = False
        
        def variableChanged(*args):
            # nonlocal returnPressed
            
            # print(self.variable.get())
            
            for variable in defaultKwArgs["variables"]:
                if variable: variable.set(self.variable.get())
                
            for f in self.onChange: f(returnPressed)
            
            # returnPressed = False
        
        dropdownStyle = ttk.Style()
        dropdownStyle.configure("TCombobox", **self.dropdownConfig)
        
        dropdown = ttk.Combobox(self, values=defaultKwArgs["options"], state="readonly", style="TCombobox")
        dropdown.grid(row=0, column=1, sticky="nsew")
        
        dropdown.bind("<<ComboboxSelected>>", comboboxSelected)
        
        self.variable.trace_add("write", variableChanged)
        self._input = dropdown
        
        if multipleValues: dropdown.set("multiple")
        else: dropdown.set(initialValue)
            
        if defaultKwArgs["readOnly"]: dropdown.configure(state="disabled")