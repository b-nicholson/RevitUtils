from pyrevit import EXEC_PARAMS, forms

# prevent the tool, await input
ungroup = forms.alert("Are you sure you want to ungroup?", options=["Yes", "No"], title="Ungroup")

# process the outcome
if ungroup == "Yes":
    EXEC_PARAMS.event_args.Cancel = False
else:
    EXEC_PARAMS.event_args.Cancel = True