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

        self.kwargs = defaultKwArgs
        self._configure = None
        self._traces = []
        
        # self.grid_columnconfigure(0, weight=1, uniform="_")
        # self.grid_columnconfigure(1, weight=1, uniform="_")
            
        labelConfig = self.labelConfig
            
        labelWidget = Label(self, text=self.label, **labelConfig)
        labelWidget.grid(row=0, column=0, sticky="nsew")
        
        def removeAllTraces(event):
            for traceData in self._traces:
                variable = traceData["variable"]
                mode = traceData["mode"]
                trace = traceData["trace"]
                
                variable.trace_remove(mode, trace)
            
        self.bind("<Destroy>", removeAllTraces)

    def appendTrace(self, variable, mode, callback):
        trace = variable.trace_add(mode, callback)
        self._traces.append({
            "variable": variable,
            "mode": mode,
            "callback": callback,
            "trace": trace
        })
        
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
        
    def getValueFromValueUnit(self, text):
        text = str(text)
        
        matchA = re.search(r"^([+-]?\d+(?:\.\d+)?)$", text.strip()) # value only
        matchB = re.search(r"^([+-]?\d+(?:\.\d+)?)\s?(\w+)$", text.strip()) # value and unit
        matchC = re.search(r"^([+-]?(?:\.\d+)?)$", text.strip()) # value without whole number
        matchD = re.search(r"^([+-]?(?:\.\d+)?)\s?(\w+)$", text.strip()) # value without whole number and unit
        
        value = 0
        
        if matchA:
            value = float(matchA.group(1))
        elif matchB:
            value = float(matchB.group(1))
        elif matchC:
            value = float(matchC.group(1))
        elif matchD:
            value = float(matchD.group(1))
            
        return value
        
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
        self._lastUnit = self.unitVar.get()
        self._input = None
        self.onChange = []
        
        unitVar = self.unitVar
        useUnit = self.useUnit
        variables = self.variables
        
        firstValue = self.values[0] if len(self.values) > 0 else None
        
        multipleValues = firstValue is not None and self.values.count(firstValue) != len(self.values)
        returnPressed = False
        unitChanged = False

        if self.type == "Text":
            self.variable = StringVar(value=firstValue if firstValue is not None else "")
        elif self.type == "Integer":
            try: firstValue = int(firstValue)
            except: firstValue = 0
            
            self.variable = IntVar(value=firstValue)
        elif self.type == "Double":
            try: firstValue = float(firstValue)
            except: firstValue = 0.0
            
            self.variable = DoubleVar(value=firstValue)
        
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
            
            value = self.variable.get()
            
            if useUnit:
                value = self.getValueFromValueUnit(self.variable.get())
                
                # print("before conversion:")
                # print(value, self._lastUnit, unitVarValue)

                value = convertPx(convertToAbsoluteSize(value, self._lastUnit), unitVarValue)
                
                # print("after conversion:")
                # print(value, self._lastUnit, unitVarValue)
                # print("-"*10)
            
            with suppress(Exception):
                if isinstance(self.variable, DoubleVar):
                    self.variable.set(float(value))
                elif isinstance(self.variable, IntVar):
                    self.variable.set(int(value))
                else:
                    self.variable.set(value)
                    
                entry.delete(0, END)
                
                if useUnit: 
                    entry.insert(0, f"{value} {unitVarValue}")
                    self._lastUnit = unitVarValue
                else: 
                    entry.insert(0, value)
            
            unitChanged = False
        
        entryConfig = self.entryConfig
        
        entry = Entry(self, **entryConfig)
        entry.grid(row=0, column=1, sticky="nsew")
        
        entry.bind("<Return>", onReturn)
        
        self.variable.trace_add("write", variableChanged)
        
        if useUnit:
            self.appendTrace(unitVar, "write", onUnitChange)
        
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
        if "readOnly" in kwargs: 
            if kwargs["readOnly"]: self._input.config(state="readonly")
            else: self._input.config(state="normal")
        
    def get(self):
        return self._input.get()

class LabeledDropdown(LabeledInput):
    globalVars = None
    
    def get(self):
        return self._input.get()
        
    def _configure(self, **kwargs):
        if "readOnly" in kwargs: 
            if kwargs["readOnly"]:self._input.state(["disabled"])
            else: self._input.state(["!disabled"])
    
    def __init__(self, master=None, **kwargs):
        globalVars = LabeledInput.globalVars
        
        defaultKwArgs = {
            "dropdownConfig": {},
            "type": "Text"
        }
        
        defaultKwArgs.update(kwargs)
        
        super().__init__(master, **defaultKwArgs)
        self._input = None
        self.onChange = []
        
        firstValue = self.values[0] if len(self.values) > 0 else None
        
        multipleValues = firstValue is not None and self.values.count(firstValue) != len(self.values)
        returnPressed = False
        modifyVariables = False
        
        self.variable = StringVar(value=firstValue if firstValue else "")
        
        def comboboxSelected(event):
            nonlocal returnPressed
            returnPressed = True
            
            self.variable.set(dropdown.get())
            
            returnPressed = False
        
        def variableChanged(*args):
            for variable in defaultKwArgs["variables"]:
                if variable: variable.set(self.variable.get())
                
            for f in self.onChange: f(returnPressed)
            
        dropdownStyle = ttk.Style()
        dropdownStyle.configure("TCombobox", **self.dropdownConfig)
        
        dropdown = ttk.Combobox(self, values=defaultKwArgs["options"], state="readonly", style="TCombobox")
        dropdown.grid(row=0, column=1, sticky="nsew")
        
        dropdown.bind("<<ComboboxSelected>>", comboboxSelected)
        
        self.variable.trace_add("write", variableChanged)
        self._input = dropdown
        
        if multipleValues: self._input.set("multiple")
        else: self._input.set(firstValue)
            
        if defaultKwArgs["readOnly"]: self._input.configure(state="disabled")
        
class LabeledCheckbox(LabeledInput):
    def get(self):
        return self.variable.get()
        
    def _configure(self, **kwargs):
        if "readOnly" in kwargs: 
            if kwargs["readOnly"]:self._input.state(["disabled"])
            else: self._input.state(["!disabled"])
        
    def __init__(self, master=None, **kwargs):
        globalVars = LabeledInput.globalVars
        
        defaultKwArgs = {}
        
        defaultKwArgs.update(kwargs)
        
        super().__init__(master, **defaultKwArgs)
        
        self._input = None
        self.onChange = []
        
        self.kwargs.update(defaultKwArgs)
        
        defaultKwArgs = self.kwargs
        
        firstValue = self.values[0] if len(self.values) > 0 else None
        
        multipleValues = firstValue is not None and self.values.count(firstValue) != len(self.values)
        returnPressed = False
        modifyVariables = False
        
        self.variable = IntVar(value=int(firstValue))

        def variableChanged(*args):
            for variable in defaultKwArgs["variables"]:
                if variable: variable.set(self.variable.get())
                
            for f in self.onChange: f(returnPressed)
            
            print(self._input.state())
        
        checkbox = ttk.Checkbutton(self, variable=self.variable, onvalue=1, offvalue=0, takefocus=False)
        checkbox.grid(row=0, column=1, sticky="nsew")
        
        self.variable.trace_add("write", variableChanged)
        self._input = checkbox

        if multipleValues: self._input.state(["alternate"])
        
        if defaultKwArgs["readOnly"]: self._input.state(["disabled"])