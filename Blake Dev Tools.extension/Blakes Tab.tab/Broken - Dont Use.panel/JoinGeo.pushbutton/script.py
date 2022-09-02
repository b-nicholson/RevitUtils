"""Joins Things"""

__title__ = 'Join\nElements'




from pyrevit import forms, revit, clr

import Autodesk.Revit.DB as DB


doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView

selected_option = forms.CommandSwitchWindow.show(
    ['Entire Model', 'Active View', 'Selection'],
    message='Select Option:',

if selected_option == 'Active View':
    selectorOption = DB.FilteredElementCollector(doc, activeView.Id)
    if forms.check_modelview(activeView):
        selected_option_active = forms.CommandSwitchWindow.show(
            ['All Visible Walls', 'By Wall Type Name', 'All Instances of Type (By New Selection)'],
            message='Select Option:',
        )

        if selected_option_active == 'By Wall Type Name':
            wherePassesFilterRequired = True
            type_collector = DB.FilteredElementCollector(doc) \
                .OfCategory(DB.BuiltInCategory.OST_Walls) \
                .WhereElementIsElementType() \
                .ToElements()
            wallTypes = []
            for t in type_collector:
                wallTypes.append(WallTypeSelector(t))
            selType = forms.SelectFromList.show(wallTypes, multiselect=False,
                                                button_name='Select Type Name')