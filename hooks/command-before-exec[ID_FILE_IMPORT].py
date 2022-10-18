# credit to aussieBIMguru https://github.com/aussieBIMguru/pyRoovit

doc = __revit__.ActiveUIDocument.Document

if doc.IsFamilyDocument:
    pass
else:
    from pyrevit import EXEC_PARAMS, forms

    cad_import = forms.alert("Importing CAD files brings a great deal of unwanted content into the project model. \n\n"
                             "Someone will need to clean up the garbage if you proceed."
                             "It is preferred to link rather than import. \n\n"
                             "Are you SURE you want to import the CAD?", options=["Yes", "No"], title="Import CAD")

    if cad_import == "Yes":
        EXEC_PARAMS.event_args.Cancel = False
    else:
        EXEC_PARAMS.event_args.Cancel = True
