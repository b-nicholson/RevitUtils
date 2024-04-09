# -*- coding: utf-8 -*-
"""Disallows Wall Joins"""

__title__ = 'Disallow\nWall Joins'

import Autodesk.Revit.DB as DB
import Autodesk.Revit.Exceptions as Exceptions
from pyrevit import forms, revit, clr, script, UI

clr.AddReference('System')
from System.Collections.Generic import List

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView


class WallTypeSelector(forms.TemplateListItem):
    @property
    def name(self):
        return "Type Name: {}".format(DB.Element.Name.GetValue(self.item))


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

nonOperableElements = 0
nonOperableGroups = []

wall_collector = []
wherePassesFilterRequired = False
isType = False
selType = ""
rawSelection = uidoc.Selection.GetElementIds()



def select_by_wall_type():
    wall_type_collector = DB.FilteredElementCollector(doc) \
        .OfCategory(DB.BuiltInCategory.OST_Walls) \
        .WhereElementIsElementType() \
        .ToElements()
    wall_types_list = []
    for wt in wall_type_collector:
        wall_types_list.append(WallTypeSelector(wt))
    select_type = forms.SelectFromList.show(wall_types_list, multiselect=False, button_name='Select Type Name')
    while select_type is None:
        forms.alert('You must make a selection. Try again?', yes=True, no=True, exitscript=True)
        select_type = forms.SelectFromList.show(wall_types_list, multiselect=False, button_name='Select Type Name')
    return select_type


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


if len(rawSelection) > 0:
    filteredSelection = DB.FilteredElementCollector(doc, rawSelection) \
        .OfCategory(DB.BuiltInCategory.OST_Walls) \
        .WhereElementIsCurveDriven() \
        .WhereElementIsNotElementType() \
        .ToElements()
    if len(filteredSelection) > 0:
        wall_collector = filteredSelection
    else:
        forms.alert('Selection must contain a wall.\n (No Groups). \n Try again.', exitscript=True)

else:
    selected_option = forms.CommandSwitchWindow.show(
        ['Entire Model', 'Active View', 'New Selection'],
        message='Select Option:',
    )

    if selected_option == 'Entire Model':
        entireModel = forms.alert("This change will be applied to the entire model, "
                                  "across all phases, design options, etc.\n\n"
                                  "This must be used with EXTREME caution\n\n"
                                  "Are you sure you want to do this?",
                                  ok=False, yes=True, no=True)
        if entireModel:
            selected_option_entireModel = forms.CommandSwitchWindow.show(
                ['By Wall Type Name', 'All Instances of Type (By New Selection)'],
                message='Select Option:',)

            if selected_option_entireModel == 'By Wall Type Name':
                selectorOption = DB.FilteredElementCollector(doc)
                wherePassesFilterRequired = True
                selType = select_by_wall_type()

            if selected_option_entireModel == 'All Instances of Type (By New Selection)':
                selectorOption = DB.FilteredElementCollector(doc)
                wherePassesFilterRequired = True
                selType = select_by_new_selection()

    if selected_option == 'Active View':
        if forms.check_modelview(activeView):
            selected_option_active = forms.CommandSwitchWindow.show(
                ['All Visible Walls', 'By Wall Type Name', 'All Instances of Type (By New Selection)'],
                message='Select Option:',
            )

            if selected_option_active == 'All Visible Walls':
                selectorOption = DB.FilteredElementCollector(doc, activeView.Id)

            if selected_option_active == 'By Wall Type Name':
                selectorOption = DB.FilteredElementCollector(doc, activeView.Id)
                wherePassesFilterRequired = True
                selType = select_by_wall_type()

            if selected_option_active == 'All Instances of Type (By New Selection)':
                selectorOption = DB.FilteredElementCollector(doc, activeView.Id)
                wherePassesFilterRequired = True
                selType = select_by_new_selection()

    if selected_option == 'New Selection':
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

            newSelectionIds = List[DB.ElementId](newSelectionIds)
            selectorOption = DB.FilteredElementCollector(doc, newSelectionIds)

    # ................................Selection occurs here........................................................
    try:
        if wherePassesFilterRequired:
            pvp = DB.ParameterValueProvider(DB.ElementId(DB.BuiltInParameter.ELEM_TYPE_PARAM))
            fRule = DB.FilterElementIdRule(pvp, DB.FilterNumericEquals(), selType.Id)
            elemFilter = DB.ElementParameterFilter(fRule)

            wall_collector = selectorOption \
                .OfCategory(DB.BuiltInCategory.OST_Walls) \
                .WherePasses(elemFilter) \
                .WhereElementIsCurveDriven() \
                .WhereElementIsNotElementType() \
                .ToElements()
        else:
            wall_collector = selectorOption \
                .OfCategory(DB.BuiltInCategory.OST_Walls) \
                .WhereElementIsCurveDriven() \
                .WhereElementIsNotElementType() \
                .ToElements()
    except NameError:
        forms.alert('Select one of the options listed.\nPlease try again.', exitscript=True)

t = DB.Transaction(doc, "Disallow Wall Joins")
t.Start()

# Iterate over walls and disallow joins on both ends
for wall in wall_collector:
    if wall is not None:
        if wall.GroupId == DB.ElementId.InvalidElementId:
            wall_is_editable = True
        else:
            group = wall.Document.GetElement(wall.GroupId)
            groupSize = group.GroupType.Groups.Size
            if groupSize == 1:
                wall_is_editable = True
            else:
                wall_is_editable = False
                nonOperableElements += 1
                nonOperableGroups.append((group.Id, group.Name))
        if wall_is_editable is True:
            DB.WallUtils.DisallowWallJoinAtEnd(wall, 0)
            DB.WallUtils.DisallowWallJoinAtEnd(wall, 1)
t.Commit()

if len(nonOperableGroups) > 0:
    output = script.get_output()
    output.print_md("# Warning!")
    output.print_md("Unable to edit " + (str(nonOperableElements)) + " walls since they are in groups with more than \
                                                                   1 instance. Their groups are listed below:")
    unique_groups = set(nonOperableGroups)
    for grp in unique_groups:
        print ("■ " + output.linkify(grp[0]) + " Type Name : " + (grp[1]))