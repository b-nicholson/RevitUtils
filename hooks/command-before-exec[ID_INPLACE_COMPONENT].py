# credit to aussieBIMguru https://github.com/aussieBIMguru/pyRoovit
from pyrevit import EXEC_PARAMS, forms

# prevent the tool, await input
mip = forms.alert("Model In-Place elements should be used sparingly. \n\n"
                  "They break inside model groups and they do not copy nicely, among many other issues. \n\n"
                  "Reserve the use of Model In Place for unique one-offs, and use families for the rest. \n\n"
                  "Are you sure this is the right tool?", options=["Yes", "No"], title="Modelling In-Place")

# process the outcome
if mip == "Yes":
    EXEC_PARAMS.event_args.Cancel = False
else:
    EXEC_PARAMS.event_args.Cancel = True
