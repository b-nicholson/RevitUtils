"""Disallows Wall Joins"""

__title__ = 'Disallow\nWall Joins'


from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, WallUtils, Transaction

doc = __revit__.ActiveUIDocument.Document


# Creating collector instance and collecting all the walls from the model
wall_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()


# Iterate over wall and collect Volume data


t = Transaction(doc, "Disallow Wall Joins")
t.Start()


for wall in wall_collector:
    WallUtils.DisallowWallJoinAtEnd(wall,0)
    WallUtils.DisallowWallJoinAtEnd(wall,1)


t.Commit()

