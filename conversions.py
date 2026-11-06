from decimal import Decimal

class Conversions:
    ppi = 96
    
    @staticmethod
    def convertPx(value=0, unit="px"):
        ppi = Conversions.ppi
        
        if unit == "in":
            return float(Decimal(str(value)) / Decimal(str(ppi)))
        elif unit == "cm":
            return float(Decimal(str(value)) / (Decimal(str(ppi)) / Decimal(str(2.54))))
        elif unit == "mm":
            return float(Decimal(str(value)) / (Decimal(str(ppi)) / Decimal(str(25.4))))
        return value
        
    @staticmethod
    def convertToAbsoluteSize(value=0, unit="px"): 
        ppi = Conversions.ppi
        
        if unit == "in":
            return float(Decimal(str(value)) * Decimal(str(ppi)))
        elif unit == "cm":
            return float(Decimal(str(value)) * Decimal(str(ppi)) / Decimal(str(2.54)))
        elif unit == "mm":
            return float(Decimal(str(value)) * Decimal(str(ppi)) / Decimal(str(25.4)))
        return value