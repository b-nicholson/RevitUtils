import Autodesk.Revit.DB as DB

from pyrevit import forms, revit, UI, clr

from Autodesk.Revit.UI.Selection import ISelectionFilter
clr.AddReference('System')
from System.Collections.Generic import List
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
activeView = doc.ActiveView


class CustomISelectionFilter(UI.Selection.ISelectionFilter):
    def __init__(self, category_name1, category_name2, category_name3):
        self.category_name1 = category_name1
        self.category_name2 = category_name2
        self.category_name3 = category_name3

    def AllowElement(self, e):
        if (e.Category.Name == self.category_name1 or
                e.Category.Name == self.category_name2 or
                e.Category.Name == self.category_name3):
            return True
        else:
            return False

    def AllowReference(self, ref, point):
        return False


def select_by_new_selection():
    elems = []
    with forms.WarningBar(title='Pick Grids or Levels to Flip:'):
        selection = uidoc.Selection.PickObjects(UI.Selection.ObjectType.Element,
                                                CustomISelectionFilter("Grids", "Levels", "Multi-segmented Grid"))
        for ref in selection:
            elems.append(DB.Document.GetElement(doc, ref))
        cleaned_selection = []
        multi_grids = []
        for source_element in elems:
            if (source_element.Category.Id == DB.Category.GetCategory(doc,
                                                                      DB.BuiltInCategory.OST_GridChains).Id):
                # multi_grids = [elem_id for elem_id in source_element.GetGridIds()]
                multi_grids.append(source_element.GetGridIds())
            else:
                cleaned_selection.append(source_element.Id)
        # multi_grids = [elem_id for elem_id in multi_grids]
        # multi_grids = multi_grids[0]
        s = set(multi_grids)
        booleans = [i in s for i in cleaned_selection]

    return s


print(select_by_new_selection())
