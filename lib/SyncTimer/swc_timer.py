from pyrevit import clr
clr.AddReference('PresentationCore')
from System.Windows.Media import Colors, ColorConverter, SolidColorBrush

gradient_step_count = 20

def make_colour(hex_code_str):
    """Converts a hex value string to a .Net SolidColour for use in WPF"""

    color_from_string = ColorConverter.ConvertFromString(hex_code_str)
    return SolidColorBrush(color_from_string)


def hex_to_rgb(value):
    """Converts a hex value string to an RGB tuple. Also converts ARGB to RGB"""

    h = value.lstrip('#')
    if len(h) == 6:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    else:
        h = h[2:]
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """Converts RGB tuples to Hex in a String"""
    return "#" + ('%02x%02x%02x' % rgb).upper()


def change_ribbon_colours(ribbon, colour):
    """Change the Revit UI Ribbon colour. Ribbon is a UIFramework.RevitRibbonControl, get it using get_ribbon()
    colour is a .Net SolidColour"""
    for tab in ribbon.Tabs:
        for panel in tab.Panels:
            panel.CustomPanelBackground = colour
            panel.CustomPanelTitleBarBackground = colour


def change_collab_tab_colour(ribbon, colour):
    """Change the colour of the Revit Collaboration tab, Synchronize Panel. Ribbon is a UIFramework.RevitRibbonControl,
    get it using get_ribbon(). Colour is a .Net SolidColour"""
    ribbon.FindTab('Collaborate').Panels[3].CustomPanelBackground = colour
    ribbon.FindTab('Collaborate').Panels[3].CustomPanelTitleBarBackground = colour


def make_collab_tab_active(ribbon):
    """Force the UI to switch to the Collaboration tab. Ribbon is a UIFramework.RevitRibbonControl,
    get it using get_ribbon()"""
    ribbon.FindTab('Collaborate').IsActive = True


def make_gradient(start_colour_str, end_colour_str):
    """Make a gradient from a start colour, and an end colour in an RGB tuple.
    Quantity of steps is defined outside of the function definition at the top of the script"""
    # https://stackoverflow.com/questions/64034165/how-to-do-linear-interpolation-with-colors
    # Starting Colour
    initial_color = hex_to_rgb(start_colour_str)
    # the final, target color
    target_color = hex_to_rgb(end_colour_str)
    gradient_colours = []
    deltas = [(target_color[i] - initial_color[i]) / gradient_step_count for i in range(3)]
    for j in range(0, gradient_step_count):
        interpolated_color = tuple([initial_color[i] + (deltas[i] * j) for i in range(3)])
        gradient_colours.append(make_colour(rgb_to_hex(interpolated_color)))
    gradient_colours.append(make_colour(rgb_to_hex(hex_to_rgb(end_colour_str))))  # yes this is stupid
    gradient_colours.pop(0)
    return gradient_colours


def get_ribbon():
    """Gets the Revit Ribbon (.Net UIFramework.RevitRibbonControl) for use in UI manipulation"""
    clr.AddReference('AdWindows')
    import Autodesk.Windows as adWin
    return adWin.ComponentManager.Ribbon


def make_times(nag_time, duration):
    """Create time values based on the number of Gradient Colours, mapped to the desired time window"""
    nag_time = int(nag_time)
    duration = int(duration)
    gradient_step_count_float = float(gradient_step_count)
    return [x / gradient_step_count_float for x in range((nag_time * gradient_step_count),
                                                         (duration * gradient_step_count), duration)]


