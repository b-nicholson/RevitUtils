# -*- coding: utf-8 -*-
"""Flips Walls, but keeps their position the same even if the location line is not centred. Use a keyboard shortcut."""

__title__ = 'Flip Walls\nWithout Moving'

import Autodesk.Revit.DB as DB
import Autodesk.Revit.Exceptions as Exceptions
from pyrevit import forms, clr, UI

clr.AddReference('System')
from System.Collections.Generic import List

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView


class CustomISelectionFilter(UI.Selection.ISelectionFilter):
    def __init__(self, category_name):
        self.category_name = category_name

    def AllowElement(self, e):
        cat = e.Category.Name
        if (cat == self.category_name):
            return True
        else:
            return False

    def AllowReference(self, ref, point):
        return False


def select_by_new_selection():

    with forms.WarningBar(title='Pick Source Wall:'):
        new_selection_completed = False
        while new_selection_completed is not True:
            try:
                select_by_type = uidoc.Selection.PickObject(UI.Selection.ObjectType.Element,
                                                            CustomISelectionFilter("Walls"))
                selection_new = (DB.Document.GetElement(doc, select_by_type))
                select_type = selection_new.WallType
                new_selection_completed = True

            except Exceptions.OperationCanceledException:
                forms.alert('Selection Cancelled. Try again?', yes=True, no=True, exitscript=True)
        return select_type


rawSelection = uidoc.Selection.GetElementIds()

if len(rawSelection) == 0:
    with forms.WarningBar(title='Select Walls'):
        selectionNew = []
        selection_completed = False
        while selection_completed is not True:
            try:
                selector = uidoc.Selection.PickObjects(UI.Selection.ObjectType.Element,
                                                       CustomISelectionFilter("Walls"))
                selection_completed = True
            except Exceptions.OperationCanceledException:
                forms.alert('Selection Cancelled. Try again?', yes=True, no=True, exitscript=True)

        for ref in selector:
            selectionNew.append(DB.Document.GetElement(doc, ref))
        newSelectionIds = []
        if len(selectionNew) > 0:
            for i in selectionNew:
                newSelectionIds.append(i.Id)

        rawSelection = List[DB.ElementId](newSelectionIds)

if rawSelection is not None:
    walls = DB.FilteredElementCollector(doc, rawSelection) \
        .OfCategory(DB.BuiltInCategory.OST_Walls) \
        .WhereElementIsCurveDriven() \
        .WhereElementIsNotElementType() \
        .ToElements()

    t = DB.Transaction(doc, "Disallow Wall Joins")
    t.Start()

    for w in walls:
        location_line = w.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM)
        current_location_line = location_line.AsInteger()
        location_line.Set(0)
        w.Flip()
        location_line.Set(current_location_line)

    t.Commit()