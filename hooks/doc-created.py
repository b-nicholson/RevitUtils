# Custom module for this system
from SyncTimer.new_doc import new_doc
from pyrevit import EXEC_PARAMS

doc = EXEC_PARAMS.event_args.Document
# Custom function shared with doc-worksharing-enabled and doc-created
new_doc(doc)
