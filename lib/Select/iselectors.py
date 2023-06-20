from pyrevit import forms, UI
import Autodesk.Revit.DB as DB
uidoc = __revit__.ActiveUIDocument
import Autodesk.Revit.Exceptions as Exceptions


class ISelectionFilerMultipleCats(UI.Selection.ISelectionFilter):
    def __init__(self, category_name):
        self.category_name = category_name

    def AllowElement(self, e):
        cat = e.Category.Name
        for c in self.category_name:
            if (cat == c):
                status = True
                break
            else:
                status = False
        return status

    def AllowReference(self, ref, point):
        return False


def select_single_w_multiple_cats_by_name(title, doc, categories_list, exit):
    with forms.WarningBar(title=title):
        new_selection_completed = False
        while new_selection_completed is not True:
            try:
                select_by_type = uidoc.Selection.PickObject(UI.Selection.ObjectType.Element,
                                                            ISelectionFilerMultipleCats(categories_list))
                selection_target = DB.Document.GetElement(doc, select_by_type)
                new_selection_completed = True

            except Exceptions.OperationCanceledException:
                try_again = forms.alert('Selection Cancelled. Try again?', yes=True, no=True, exitscript=exit)
                if not try_again:
                    new_selection_completed = True
    return selection_target
