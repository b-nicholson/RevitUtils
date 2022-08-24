"""Disallows Wall Joins"""

__title__ = 'Disallow\nWall Joins'

import Autodesk.Revit.DB as DB
from pyrevit import revit

from pyrevit import forms

doc = __revit__.ActiveUIDocument.Document

wall_collector = []

rawSelection = revit.get_selection()

for s in rawSelection:
    id = [s.Id]

if len(rawSelection) > 0:
    filteredSelection = DB.FilteredElementCollector(doc, id) \
                    .OfCategory(DB.BuiltInCategory.OST_Walls) \
                    .WhereElementIsCurveDriven() \
                    .WhereElementIsNotElementType()\
                    .ToElements()
    if len(rawSelection) > 0:
        wall_collector = filteredSelection
        t = DB.Transaction(doc, "Disallow Wall Joins")
        t.Start()

        # Iterate over walls and disallow joins on both ends
        for wall in wall_collector:
            if wall is not None:
                DB.WallUtils.DisallowWallJoinAtEnd(wall,0)
                DB.WallUtils.DisallowWallJoinAtEnd(wall,1)
        t.Commit()

