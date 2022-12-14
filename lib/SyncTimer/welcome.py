def print_welcome():

    from pyrevit import script

    output = script.get_output()
    output.print_html("<h1><strong>Welcome!</strong></h1>\
    <p>&nbsp;</p>\
    <p>Thanks for installing my extension. It is currently, and probably will forever be, a work in progress. If something goes wrong, or if you have any suggestions please let me know.</p>\
    <p>It installs a new Tab at the top of the Revit Ribbon called <em>Blake&#39;s Tab. </em>Inside are a variety of small tools that I will do my best to keep adding to.</p>\
    <p>&nbsp;</p>\
    <p>There are some utilities that work in the background which modify the way Revit operates, but are not immediately obvious that they&#39;re running. They are explained below:</p>\
    <p>&nbsp;</p>\
    <p><strong>Synchronize With Central Timer</strong></p>\
    <ul>\
    <li>\
    This plugin will gradually change the colour of your <em>Application Ribbon</em> if you have not synced a workshared document in a user-specified duration. If you exceed the time, it will automatically switch your active tab to <em>Collaborate</em>, and highlight the <em>Synchronize</em> panel.\
    </li>\
    <li>\
    You can adjust the timing and colour settings within the <em>Sync With Central Timer Settings</em> button inside of <em>Blake&#39;s Tab.</em>\
    </li>\
    </ul>\
    <p><strong>Import CAD</strong></p>\
    <ul>\
        <li>If you try to import a CAD file inside of a project (not a family) it will produce a warning, but still allow you to do it if you REALLY need to. (but why!?)</li>\
    </ul>\
    <p><strong>Model In Place</strong></p>\
    <ul>\
        <li>If you try to create a Model in Place Component it will produce a warning, but still allow you to do it. This is a tool for mindfulness.</li>\
    </ul>\
    <p><strong>Ungroup Groups</strong></p>\
    <ul>\
        <li>I dont know about you, but I misclick this a lot. No idea who thought having it beside Edit Group in the UI was a good idea. Not noticing it was accidentally ungrouped has bad consequences. The plugin will give you a warning before ungrouping.</li>\
    </ul>\
    <p>&nbsp;</p>\
    ")
