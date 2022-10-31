# -*- coding: utf-8 -*-
"""Flips the 2D ends of Levels & Grids"""

__title__ = 'Flip 2D Datum Ends'

import Autodesk.Revit.DB as DB

from pyrevit import forms, UI, script

from Autodesk.Revit.UI.Selection import ISelectionFilter

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView


class CustomISelectionFilter(UI.Selection.ISelectionFilter):
    def __init__(self, category_name1, category_name2):
        self.category_name1 = category_name1
        self.category_name2 = category_name2

    def AllowElement(self, e):
        cat = e.Category.Name
        if (cat == self.category_name1 or
                cat == self.category_name2):
            return True
        else:
            return False

    def AllowReference(self, ref, point):
        return False


def select_by_new_selection():
    elems = []
    with forms.WarningBar(title='Pick Grids or Levels to Modify:'):
        selection = uidoc.Selection.PickObjects(UI.Selection.ObjectType.Element,
                                                CustomISelectionFilter("Grids", "Levels"))
        for ref in selection:
            elems.append(DB.Document.GetElement(doc, ref))
        cleaned_selection = []
        multi_segment_flag = False
        for source_element in elems:
            if source_element.get_Parameter(DB.BuiltInParameter.DATUM_VOLUME_OF_INTEREST).IsReadOnly:
                multi_segment_flag = True
            else:
                cleaned_selection.append(source_element)
        if multi_segment_flag:
            forms.alert('Multi Segmented Grids dont do anything properly.\n'
                        'The script will ignore them.')
    return cleaned_selection

nonOperableGrids = 0
nonOperableGroups = []

grid_selector = select_by_new_selection()

t = DB.Transaction(doc, "Show Both Datum Bubbles")
t.Start()
for grid in grid_selector:
    grid_is_editable = False
    if grid.GroupId == DB.ElementId.InvalidElementId:
        grid_is_editable = True

    else:
        group = grid.Document.GetElement(grid.GroupId)
        group_type = group.GroupType
        groupSize = group.GroupType.Groups.Size
        if groupSize == 1:
            grid_is_editable = True
        if groupSize > 1:
            nonOperableGrids += 1
            nonOperableGroups.append((group.Id, group.Name))

    if grid_is_editable is True:
        grid.HideBubbleInView(DB.DatumEnds.End0, activeView)
        grid.ShowBubbleInView(DB.DatumEnds.End1, activeView)


t.Commit()

if len(nonOperableGroups) > 0:
    output = script.get_output()
    output.print_md("# Warning!")
    output.print_md("Unable to edit " + (str(nonOperableGrids)) + " grids/levels since they are in groups with more \
                                                                    than 1 instance. Their groups are listed below:")
    unique_groups = set(nonOperableGroups)
    for grp in unique_groups:
        print ("■ " + output.linkify(grp[0]) + " Type Name : " + (grp[1]))