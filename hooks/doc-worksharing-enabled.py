# Custom module for this system
from SyncTimer.new_doc import new_doc
from pyrevit import EXEC_PARAMS

doc = EXEC_PARAMS.event_args.GetDocument()
# Custom function shared with doc-opened and doc-created
new_doc(doc)
