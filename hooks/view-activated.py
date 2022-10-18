# This hook can be removed if the app idling hook has the memory leak fixed
# https://github.com/eirannejad/pyRevit/issues/1252

# Custom module for this system
from SyncTimer.ui_change import ui_change
from pyrevit import EXEC_PARAMS

doc = EXEC_PARAMS.event_args.Document
# Custom function shared with doc-changed
ui_change(doc)
