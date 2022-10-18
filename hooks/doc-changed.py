# This hook can be changed to the app idling hook if the memory leak is fixed
# https://github.com/eirannejad/pyRevit/issues/1252

# Custom module for this system
from SyncTimer.ui_change import ui_change
from pyrevit import EXEC_PARAMS

doc = EXEC_PARAMS.event_args.GetDocument()
# Custom function shared with view-activated
ui_change(doc)
