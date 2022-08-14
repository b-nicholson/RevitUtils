"""Moves Room Tags to Room Calculation Point"""

__title__ = 'Move\nRoom Tags'


from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, ElementTransformUtils, Transaction
from pyrevit import revit

doc = __revit__.ActiveUIDocument.Document
curview = revit.active_view

# Creating collector instance and collecting all the walls from the model
tag_collector = FilteredElementCollector(doc, curview.Id).OfCategory(BuiltInCategory.OST_RoomTags).WhereElementIsNotElementType()


# Iterate over room tags and collect room tag location and host room s

tagLocation = []
roomLocation = []
moveLocation = []

t = Transaction(doc, "Update Sheet Parmeters")
t.Start()


for tag in tag_collector:
    if tag.HasLeader == False:
        ElementTransformUtils.MoveElement(doc,tag.Id,tag.Room.Location.Point - tag.Location.Point)




t.Commit()

#print(tagLocation)
#print(roomLocation)
#print(moveLocation)