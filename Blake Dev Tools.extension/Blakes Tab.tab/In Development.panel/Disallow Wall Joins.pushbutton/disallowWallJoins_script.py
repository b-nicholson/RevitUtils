"""Disallows Wall Joins"""

__title__ = 'Disallow\nWall Joins'

import Autodesk.Revit.DB as DB

from pyrevit import forms, revit, clr

clr.AddReference('System')
from System.Collections.Generic import List

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView


class WallTypeSelector(forms.TemplateListItem):
    @property
    def name(self):
        return "Type Name: {}".format(DB.Element.Name.GetValue(self.item))


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
    is_wall_type = False
    while is_wall_type is not True:
        with forms.WarningBar(title='Pick Source Wall:'):
            source_element = revit.pick_element()
            try:
                select_type = source_element.WallType
                is_wall_type = True
            except AttributeError:
                forms.alert('Selection must be a wall. Try again?', yes=True, no=True, exitscript=True)
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
        forms.alert('Selection must contain a wall. Try again.', exitscript=True)

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
            selectorOption = DB.FilteredElementCollector(doc)
            selected_option_entireModel = forms.CommandSwitchWindow.show(
                ['By Wall Type Name', 'All Instances of Type (By New Selection)'],
                message='Select Option:',
            )

            if selected_option_entireModel == 'By Wall Type Name':
                wherePassesFilterRequired = True
                selType = select_by_wall_type()

            if selected_option_entireModel == 'All Instances of Type (By New Selection)':
                wherePassesFilterRequired = True
                selType = select_by_new_selection()

    if selected_option == 'Active View':
        selectorOption = DB.FilteredElementCollector(doc, activeView.Id)
        if forms.check_modelview(activeView):
            selected_option_active = forms.CommandSwitchWindow.show(
                ['All Visible Walls', 'By Wall Type Name', 'All Instances of Type (By New Selection)'],
                message='Select Option:',
            )

            if selected_option_active == 'By Wall Type Name':
                wherePassesFilterRequired = True
                selType = select_by_wall_type()

            if selected_option_active == 'All Instances of Type (By New Selection)':
                wherePassesFilterRequired = True
                selType = select_by_new_selection()

    if selected_option == 'New Selection':
        with forms.WarningBar(title='Select Walls'):
            selectionNew = revit.pick_elements()
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
        DB.WallUtils.DisallowWallJoinAtEnd(wall, 0)
        DB.WallUtils.DisallowWallJoinAtEnd(wall, 1)

t.Commit()
