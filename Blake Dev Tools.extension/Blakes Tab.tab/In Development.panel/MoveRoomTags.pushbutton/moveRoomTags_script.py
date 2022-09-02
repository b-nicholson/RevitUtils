"""Moves Room Tags to Room Location Point in Active View"""

__title__ = 'Move\nRoom Tags'

import Autodesk.Revit.DB as DB
from pyrevit import revit

doc = __revit__.ActiveUIDocument.Document
curView = revit.active_view

# Creating collector instance and collecting all the room tags from the active view
tag_collector = DB.FilteredElementCollector(doc, curView.Id)\
                .OfCategory(DB.BuiltInCategory.OST_RoomTags)\
                .WhereElementIsNotElementType()

t = DB.Transaction(doc, "Move Room Tags")
t.Start()

for tag in tag_collector:
    if not tag.HasLeader:
        DB.ElementTransformUtils.MoveElement(doc,tag.Id,tag.Room.Location.Point - tag.Location.Point)

t.Commit()
