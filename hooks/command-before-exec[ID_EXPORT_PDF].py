import Autodesk.Revit.DB as DB

doc = __revit__.ActiveUIDocument.Document

worksets = DB.FilteredWorksetCollector(doc).ToWorksets()


closed_workset = []
for w in worksets:
    if w.Kind == DB.WorksetKind.UserWorkset:
        if w.IsOpen == False:
            closed_workset.append(w.Name)

from pyrevit import EXEC_PARAMS, forms

if closed_workset:
    formatted_list = "\n".join(closed_workset)

    warning = "The following worksets are closed: \n\n" + formatted_list + "\n\n Are you sure you want to print?"
    print_warning = forms.alert(warning, options=["Yes", "No"], title="Closed Worksets")

    if print_warning == "Yes":
        EXEC_PARAMS.event_args.Cancel = False
    else:
        EXEC_PARAMS.event_args.Cancel = True
