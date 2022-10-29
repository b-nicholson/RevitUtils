from pyrevit.userconfig import user_config

try:
    warning_colour_str = user_config.swc_timer.get_option("warning_colour", "#FF0000")
except AttributeError:
    from SyncTimer.welcome import print_welcome
    print_welcome()
    user_config.add_section("swc_timer")
