import Autodesk.Revit.DB as DB
app = __revit__.Application

def convert_mm_or_in_to_internal_units(length, unit_type):
    rvt_year = int(app.VersionNumber)
    if rvt_year < 2022:
        if unit_type == 1:
            old_units = DB.DisplayUnitType.DUT_MILLIMETER
        else:
            old_units = DB.DisplayUnitType.DUT_DECIMAL_INCHES
        return DB.UnitUtils.Convert(length, old_units, DB.DisplayUnitType.DUT_DECIMAL_FEET)
    else:
        if unit_type == 1:
            new_units = DB.UnitTypeId.Millimeters
        else:
            new_units = DB.UnitTypeId.Inches
        return DB.UnitUtils.ConvertToInternalUnits(length, new_units)