class PropertyData:
    def __init__(self, Object=None, name="", value=None, **kwargs):
        self.lastValue = ""
        self.readOnly = kwargs["readOnly"] if "readOnly" in kwargs else False
        self.variable = kwargs["variable"] if "variable" in kwargs else None
        self.useUnit = kwargs["useUnit"] if "useUnit" in kwargs else None
        self.valueUnit = kwargs["valueUnit"] if "valueUnit" in kwargs else None
        self.options = kwargs["options"] if "options" in kwargs else []
        self.useOptions = kwargs["useOptions"] if "useOptions" in kwargs else False
        
        self.name = name
        self.value = value if value else None
        self.object = Object
        
        if self.value:
            if self.variable:
                self.variable.set(self.value)
        
        if self.variable:
            def setValue(*args):
                self.value = self.variable.get()
                
            self.variable.trace_add("write", setValue)
            
            if self.value is None: setValue()
        
    def __repr__(self):
         return(str(vars(self)))
        
class Properties:
    def __init__(self, cnf=None, **categories):
        if cnf is None: cnf = {}
        categories.update(cnf)
        
        self._properties = categories
        self.onChange = []
        
    def __repr__(self):
        return str(self._properties)
        
    def get(self, category=None):
        if category: return self._properties[category]
        return self._properties
        
    def update(self, cnf=None, **categories):
        if cnf is None: cnf = {}
        categories.update(cnf)
        self._properties.update(categories)
    