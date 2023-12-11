from libqtile import bar, layout, widget, hook
from libqtile.config import Click, Drag, Group, Key, Match, Screen, ScratchPad, DropDown
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal

import os, subprocess

mod = "mod4"
terminal = guess_terminal()

def switch_group(k):
    @lazy.function
    def inner(qtile):
        groups = qtile.groups
        L = len(groups)
        i = groups.index(qtile.current_group)
        j = len(qtile.current_group.windows) != 0

        while len(groups[i % L].windows) == 0:
            i += k
        qtile.current_screen.set_group(groups[(i + j*k) % L])

    return inner

switch_to_prev_group = switch_group(-1)
switch_to_next_group = switch_group(1)

t = list([Group(i) for i in "123456789"] + [
        ScratchPad("0", [
            DropDown('launch', 'alacritty', 
                     x=0.12, y=0.02, width=0.75, height=0.96, on_focus_lost_hide=True),
            DropDown('music-firefox', 'firefox --new-instance --profile /home/miky/.mozilla/firefox/hrzmgere.Scratchpad', 
                     x=0.06, y=0.06, width=0.88, height=0.88, on_focus_lost_hide=False),
        ])    
    ])

groups = t

#+ [
#            ScratchPad("Scratchpad", [
#                DropDown('launch', 'alacritty', x=0.12, y=0.02, width=0.75, height=0.95)
#            ])    
#        ]

keys = [
    # A list of available commands that can be bound to keys can be found
    # at https://docs.qtile.org/en/latest/manual/config/lazy.html
    # Switch between groups
    Key([mod], "Tab", switch_to_next_group, desc="Move to next group"),
    Key([mod, "shift"], "Tab", switch_to_prev_group, desc="Move to next group"),
    # Switch between windows
    Key([mod], "h", lazy.layout.left(), desc="Move focus to left"),
    Key([mod], "l", lazy.layout.right(), desc="Move focus to right"),
    Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
    Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
    Key(["mod1"], "h", lazy.layout.move_left(), desc="Move focus to left"),
    Key(["mod1"], "l", lazy.layout.move_right(), desc="Move focus to right"),
    Key(["mod1"], "j", lazy.layout.move_down(), desc="Move focus to left"),
    Key(["mod1"], "k", lazy.layout.move_up(), desc="Move focus to right"),
    # Key([mod], "space", lazy.layout.next(), desc="Move window focus to other window"),
    # Move windows between left/right columns or move up/down in current stack.
    # Moving out of range in Columns layout will create new column.
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Move window to the left"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Move window to the right"),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move window down"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),
    # Grow windows. If current window is on the edge of screen and direction
    # will be to screen edge - window would shrink.
    Key([mod, "mod1"], "h", lazy.layout.grow_left(), desc="Grow window to the left"),
    Key([mod, "mod1", "shift"], 
        "h", lazy.layout.shrink_left(), desc="Shrink window to the left"),
    Key([mod, "mod1"], "l", lazy.layout.grow_right(), desc="Grow window to the right"),
    Key([mod, "mod1", "shift"], 
        "l", lazy.layout.shrink_right(), desc="Shrink window to the right"),
    Key([mod, "mod1"], "j", lazy.layout.grow_down(), desc="Grow window to the left"),
    Key([mod, "mod1", "shift"], 
        "j", lazy.layout.shrink_down(), desc="Shrink window to the left"),
    Key([mod, "mod1"], "k", lazy.layout.grow_up(), desc="Grow window to the right"),
    Key([mod, "mod1", "shift"], 
        "k", lazy.layout.shrink_up(), desc="Shrink window to the right"),
    Key([mod, "mod1"], "j", lazy.layout.grow_down(), desc="Grow window down"),
    Key([mod, "mod1"], "k", lazy.layout.grow_up(), desc="Grow window up"),
    Key([mod], "n", lazy.layout.normalize(), desc="Reset all window sizes"),
    # Flip windows at the same level of the binary tree
    # Key([mod, "mod1"], "j", lazy.layout.flip_down()),
    # Key([mod, "mod1"], "k", lazy.layout.flip_up()),
    # Key([mod, "mod1"], "h", lazy.layout.flip_left()),
    # Key([mod, "mod1"], "l", lazy.layout.flip_right()),
    # Key([mod], "Return", lazy.layout.toggle_split()),
    # Toggle between split and unsplit sides of stack.
    # Split = all windows displayed
    # Unsplit = 1 window displayed, like Max layout, but still with
    # multiple stack panes
    Key(
        [mod, "shift"],
        "p",
        lazy.layout.toggle_split(),
        desc="Toggle between split and unsplit sides of stack",
    ),
    Key([mod, "shift"], "Return", lazy.spawn(terminal), desc="Launch terminal"),
    # Toggle between different layouts as defined below
    Key([mod], "space", lazy.next_layout(), desc="Toggle between layouts"),
    Key([mod, "shift"], "w", lazy.window.kill(), desc="Kill focused window"),
    Key([mod, "control"], "r", lazy.reload_config(), desc="Reload the config"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
    Key([mod, "shift"], "d", lazy.spawncmd(), desc="Spawn a command using a prompt widget"),
    Key([mod], "d", lazy.spawn("rofi -modi drun -show drun"), desc="Spawn a desktop entry"),

    # audio
    Key(
        [], "XF86AudioRaiseVolume",
        lazy.spawn("amixer -c 0 -q set Master 2dB+")
    ),
    Key(
        [], "XF86AudioLowerVolume",
        lazy.spawn("amixer -c 0 -q set Master 2dB-")
    ),
    Key(
        [mod, "control"], "Right",
        lazy.spawn("playerctl next")
    ),
    Key(
        [mod, "control"], "Left",
        lazy.spawn("playerctl previous")
    ),
    Key(
        [mod, "control"], "Space",
        lazy.spawn("playerctl play-pause")
    ),
    Key(
        [mod], "Return",
        lazy.group["0"].dropdown_toggle("launch")
    ),
    Key(
        [mod], "m",
        lazy.group["0"].dropdown_toggle("music-firefox")
    )
]

for i in groups:
    keys.extend(
        [
            # mod1 + letter of group = switch to group
            Key(
                [mod],
                i.name,
                lazy.group[i.name].toscreen(),
                desc="Switch to group {}".format(i.name),
            ),
            # mod1 + shift + letter of group = switch to & move focused window to group
            Key(
                [mod, "shift"],
                i.name,
                lazy.window.togroup(i.name, switch_group=True),
                desc="Switch to & move focused window to group {}".format(i.name),
            ),
            # Or, use below if you prefer not to switch to that group.
            # # mod1 + shift + letter of group = move focused window to group
            # Key([mod, "shift"], i.name, lazy.window.togroup(i.name),
            #     desc="move focused window to group {}".format(i.name)),
        ]
    )

from qtail import qTail

layouts = [
    qTail(margin = 10),
    layout.Bsp(
        border_focus='#88c0d0',
        margin=10
    ),
    # layout.Columns(border_focus_stack=["#d75f5f", "#8f3d3d"], border_width=4),
    layout.Max(margin = 10),

    # Try more layouts by unleashing below layouts.
    # layout.Stack(num_stacks=2),
    # layout.Matrix(),
    # layout.MonadTall(),
    # layout.MonadWide(),
    # layout.RatioTile(),
    # layout.Tile(),
    # layout.TreeTab(),
    # layout.VerticalTile(),
    # layout.Zoomy(),
    # layout.Floating(),
]

# xft:Montserrat Alternates:size=11:antialias=true
widget_defaults = dict(
    font="Montserrat Alternates",
    fontsize=15,
    padding=3,
)
extension_defaults = widget_defaults.copy()

colorPalette = {
    'main': '#F28B0C',
    'main2': '#058FE6',
    'white': '#F0F3F5',
    'lightGrey': '#2A3D45',
    'darkGrey': '#162024',
    'lightGrey2': '#C8CBCC',
    'aurora1': "#bf616a"
}

# U+E634:  in 3270Medium Nerd Font
from widget_wrappers import MyWrapper, MyCenteredWrapper

screens = [
    Screen(
        bottom=bar.Bar(
            [
                widget.Spacer(
                    length=5,
                    background = colorPalette['darkGrey']
                ),
                widget.Image(
                    filename='~/.config/qtile/arch.png',
                    background= colorPalette['darkGrey']
                ),
                widget.Spacer(
                    length=5,
                    background = colorPalette['darkGrey']
                ),
                widget.Image(
                    filename='~/.config/qtile/curve-LBb.jpg',
                ),
                widget.GroupBox(
                    font="Montserrat Alternates Regular",
                    fontsize = 15,
                    margin_y = 5,
                    margin_x = 0,
                    padding_y = 44,
                    padding_x = 3,
                    borderwidth = 3,
                    spacing = 10,
                    active = colorPalette['main2'],
                    inactive = colorPalette['lightGrey2'],
                    highlight_color = '#42473F', #colorPalette['darkMain2'],
                    highlight_method = "line",
                    this_current_screen_border = colorPalette['main'],
                    background = colorPalette['lightGrey'],
                    urgent_border = colorPalette['aurora1'],
                ),
                widget.Image(
                    filename='~/.config/qtile/line-7bB.jpg',
                    background="#353446"
                ),
                widget.CurrentLayout(
                    foreground = colorPalette['white'],
                    background = colorPalette['darkGrey'],
                ),
                widget.Spacer(
                    length=5,
                    background = colorPalette['darkGrey']
                ),
                widget.Image(
                    filename='~/.config/qtile/curve-LBb.jpg',
                    background="#353446"
                ),
                # widget.Spacer(length=10),
                # widget.Prompt(),
                widget.Spacer(length=bar.STRETCH),
                #widget.TextBox("default config", name="default"),
                #widget.TextBox("Press &lt;M-r&gt; to spawn", foreground="#d75f5f"),

                #TextWrapperPrototype(
                #    "!!!",
                #    background = colors2[22],
                #    padding = 10
                #),
                widget.Image(
                    filename='~/.config/qtile/curve-JbB.jpg',
                ),
                MyWrapper(
                    Widget = widget.Clock, 
                    tollerance = 30,
                    format="   %A %b %d" + " " * 2 + "  %H:%M:%S",
                    font="Montserrat Alternates",
                    fontsize = 16,
                    foreground = colorPalette['white'],
                    background = colorPalette['darkGrey'],
                    padding = 10
                ), 
                widget.Image(
                    filename='~/.config/qtile/curve-LBb.jpg',
                ),
                widget.Spacer(length=bar.STRETCH),
                widget.Systray(
                ),
                widget.Spacer(
                    length=10,
                    background = colorPalette['lightGrey']
                ),
                widget.Image(
                    filename='~/.config/qtile/curve-JbB.jpg',
                ),
                widget.Spacer(
                    length=5,
                    background = colorPalette['darkGrey']
                ),
                widget.WidgetBox(
                    background = colorPalette['darkGrey'],
                    font="SauceCodePro Nerd Font Mono",
                    fontsize=20,
                    text_closed = "",
                    text_open = "",
                    widgets=[
                        widget.Image(
                            filename='~/.config/qtile/line-FBb.jpg',
                        ),
                        widget.CPU(),
                        widget.Image(
                            filename='~/.config/qtile/line-FbB.jpg',
                        ),
                    ]
                ),
                widget.Image(
                    filename='~/.config/qtile/line-FBb.jpg',
                ),
                widget.TextBox("",
                    background = colorPalette['lightGrey'],
                    font="SauceCodePro Nerd Font Mono",
                    fontsize=18,
                    padding = 0
                ),
                MyCenteredWrapper(
                    Widget = widget.Volume,
                    tollerance = 1,
                    background = colorPalette['lightGrey'],
                    fmt=' {}',
                    padding = 10
                ),
                widget.Image(
                    filename='~/.config/qtile/sep1.jpg',
                ),
                MyCenteredWrapper(
                    Widget = widget.Battery,
                    tollerance = 24,
                    format = '{char} {percent:1.0%} {hour:d}:{min:02d}', 
                    low_percentage = 0.3,
                    charge_char = "" + ' '*2,
                    discharge_char="" + ' '*2,
                    background = colorPalette['lightGrey'],
                    padding = 0,
                ),
                widget.Image(
                    filename='~/.config/qtile/sep1.jpg',
                ),
                MyCenteredWrapper(
                    Widget = widget.ThermalZone,
                    tollerance = 10,
                    background = colorPalette['lightGrey'],
                    padding = 0
                ),
                widget.Image(
                    filename='~/.config/qtile/curve-JbB.jpg',
                ),
                widget.QuickExit(
                    background = colorPalette['darkGrey'],
                    foreground = colorPalette['white']
                ),
            ],
            30,
            background = colorPalette['lightGrey'],
            opacity=0.9,
            margin = [0,10,6,10],
            border_width=[4, 4, 4, 4],  # Draw top and bottom borders
            # border_color = [color3['main4']] * 4
            border_color=[colorPalette['darkGrey']] * 4,
        ),
    ),
]
screen_res = {
    'width': 1920, 
    'height': 1080
}


# Drag floating layouts.
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

@hook.subscribe.startup_once
def autostart():
    home = os.path.expanduser('~/.config/qtile/autostart.sh')
    subprocess.Popen([home])

dgroups_key_binder = None
dgroups_app_rules = []  # type: list
follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
floating_layout = layout.Floating(
    float_rules=[
        # Run the utility of `xprop` to see the wm class and name of an X client.
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
    ]
)
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True

# If things like steam games want to auto-minimize themselves when losing
# focus, should we respect this or not?
auto_minimize = True

# When using the Wayland backend, this can be used to configure input devices.
wl_input_rules = None

# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, GitHub issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "LG3D"
