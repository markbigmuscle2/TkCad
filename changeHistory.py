class HistoryManager:
    globalVars = None
    
    def __init__(self):
        self.undoStack = []
        self.redoStack = []
        self.onUndo = []
        self.onRedo = []
        self.onDo = []
        
    def _debug(self, cmd):
        print("cmd:", cmd)
        print("undo stack:", len(self.undoStack))
        print("redo stack:", len(self.redoStack))
        print("-"*10)
        
    def do(self, cmd):
        self.undoStack.append(cmd)
        self.redoStack = []
        
        for f in self.onDo: f(cmd)
        
    def undo(self, event = None):
        if len(self.undoStack) == 0: return
        
        cmd = self.undoStack.pop()
        cmd.undo()
        self.redoStack.append(cmd)
        
        for f in self.onUndo: f(cmd)

    def redo(self, event = None):
        if len(self.redoStack) == 0: return
        
        cmd = self.redoStack.pop()
        cmd.redo()
        self.undoStack.append(cmd)
        
        for f in self.onRedo: f(cmd)
        
class Command:
    propertyMenu = None
    
    def __init__(self, **data):
        for key in data: setattr(self, key, data[key])
        
    def undo(self):
        self._undo()
        
    def redo(self):
        self._redo()
        
class DrawCommand(Command):
    def __init__(self, **data):
        super().__init__(**data)
        
    def _undo(self):
        propertyMenu = Command.propertyMenu
        
        self.drawing.delete()
        
        propertyMenu.startSelection()
        
        propertyMenu.clearSelection()
        
        propertyMenu.finishSelection()
        
    def _redo(self):
        propertyMenu = Command.propertyMenu
        
        propertyMenu.finishSelection()
        
        self.drawing.redraw()
        
        propertyMenu.startSelection()
        
        propertyMenu.updateSelection(self.drawing, ctrlKeyPressed=False)
        
class PropertyChangedCommand(Command):
    def __init__(self, **data):
        super().__init__(**data)
        
    def _applyState(self, targetValues, fallback):
        propertyMenu = Command.propertyMenu
        name = self.name
        properties = self.properties
        values = self.values
        lastValues = self.lastValues
        
        drawings = list(map(lambda prop: prop.object, properties))
        
        # print("values:", {key.object.id: value for key, value in values.items()})
        # print("last values:", {key.object.id: value for key, value in lastValues.items()})
        
        # for prop in properties:
            # if (prop not in values) or (prop not in lastValues): 
                # continue
            
            # prop.value = targetValues[prop]
            
            # if prop.variable: 
                # prop.variable.set(prop.value)
            
            # for f in prop.object.properties.onChange: 
                # f(prop, prop.value)
                
        for prop, value in targetValues.items():
            if prop not in targetValues: continue
            
            prop.value = value
            
            if prop.variable: 
                prop.variable.set(prop.value)
                
            print(prop.object.id)
            print(prop.value)
            print("-"*10)
            
            for f in prop.object.properties.onChange: 
                f(prop, prop.value)
                
        propertyMenu.finishSelection()
        propertyMenu.startSelection()
        propertyMenu.updateSelection(*drawings, ctrlKeyPressed=False, reloadSameSelection=True)

        uniqueValues = set(targetValues.values())
        
        if len(uniqueValues) > 1:
            propertyMenu.updateProperty(name, "multiple")
        else:
            propertyMenu.updateProperty(name, fallback)
        
    def _undo(self):
        self._applyState(self.lastValues, self.lastInputValue)
        
    def _redo(self):
        self._applyState(self.values, self.inputValue)

class EraseCommand(Command):
    def __init__(self, **data):
        super().__init__(**data)
        
    def _undo(self):
        from geometry import Drawing
        
        propertyMenu = Command.propertyMenu
        
        propertyMenu.finishSelection()
        
        for drawing in self.drawings:
            drawing.redraw()

        propertyMenu.startSelection()
        
        selection = [drawing for drawing in self.drawings if isinstance(drawing, Drawing)]
        
        propertyMenu.updateSelection(*selection, ctrlKeyPressed=False)
        
    def _redo(self):
        propertyMenu = Command.propertyMenu
        
        for drawing in self.drawings:
            drawing.delete()
            
        propertyMenu.clearSelection()
            
class DimensionCommand(Command):
    def __init__(self, **data):
        super().__init__(**data)
        
    def _undo(self):
        self.dimension.delete()
        
    def _redo(self):
        globalVars = HistoryManager.globalVars
        globalVars.toolObject.mode.set(self.mode)
        globalVars.dimensionSelectionType.set(self.dimensionSelectionType)
        self.dimension.redraw()