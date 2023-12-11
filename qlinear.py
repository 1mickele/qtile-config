from __future__ import annotations
from typing import TYPE_CHECKING
from enum import Enum
from itertools import accumulate

from libqtile.command.base import expose_command
from libqtile.layout.base import Layout

from libqtile.log_utils import logger

if TYPE_CHECKING:
    from typing import Any, Generator, Self

    from libqtile.backend.base import Window
    from libqtile.config import ScreenRect
    from libqtile.group import _Group

class Way(Enum):
    TORIGHT = 1
    TOLEFT = 0

class Attr:
    x = 0
    y = 1
    w = 2
    h = 3


class LinTail(Layout):
    def __init__ (self, **config):
        Layout.__init__(self, **config)
        # self.add_defaults(Bsp.defaults) # finally
        self.margin = config['margin']
        self.windows = []
        self.specs : [[float, float, float, float]] = [] # x,y,w,h
        self.way = Way.TORIGHT
        self.current = 0
        self.view_offset : float = 0.0
        self.border_focus = "#FF0000"
        self.border_normal = "#DDEEDD"
        self.border_on_single = False
        self.border_width = 2
        self.width_ratio = 0.4

    def clone(self, group: _Group) -> Self:
        c = Layout.clone(self, group)
        c.windows = []
        c.specs = []
        c.current = 0
        c.view_offset = 0.0
        c.width_ratio = 0.5
        return c

    def get_windows(self):
        return self.windows

    def focus(self, client: Window) -> None:
        self.current = self.windows.index(client)
        self._keep_inview()
        self._edge_fill()

    def add_client(self, client: Window) -> None:
        index = self.current + self.way.value
        if len(self.windows) <= 1:
            self.windows.insert(index, client)
            self.specs.insert(index, None) #?
            self._edge_cases()
        else:
            curr_client = self.specs[self.current]
            self.windows.insert(index, client)
            # refactor this shit
            if self.way == Way.TORIGHT:
                self.specs.insert(index, [curr_client[Attr.x] + curr_client[Attr.w], 0.0, 
                                          self.width_ratio, 1.0]) 
                for s in self.specs[index+1:]:
                    s[Attr.x] += self.width_ratio
            else: 
                self.specs.insert(index, [curr_client[Attr.x] - self.width_ratio, 0.0, 
                                          self.width_ratio, 1.0]) 
                for s in self.specs[:index]:
                    s[Attr.x] -= self.width_ratio
        self.current = index

    def remove(self, client):
        index = self.windows.index(client)
        for s in self.specs[index+1:]:
            s[Attr.x] -= self.specs[index][Attr.w]
        del self.windows[index], self.specs[index]
        self._edge_cases()

    def _in_view(self, client: Window) -> bool:
        target = self.specs[self.windows.index(client)]
        if (self.view_offset - target[2] < target[0] < self.view_offset + 1):
            return True
        return False

    def _keep_inview(self):
        target = self.specs[self.current]
        if target[0] < self.view_offset:
            self.view_offset = target[0]
        elif ((d := target[0] + target[2]) > self.view_offset + 1.0):
            self.view_offset = d - 1.0
        
    def _edge_cases(self):
        if len(self.windows) == 1:
            self.specs[0] = [0,0,1,1]
            return True
        elif len(self.windows) == 2:
            self.specs = [[0,0,self.width_ratio, 1],
                [self.width_ratio, 0, self.width_ratio, 1]]
            return True
        return False

    def _edge_fill(self):
        if (d := (self.specs[-1][Attr.x] + self.specs[-1][Attr.w])) - \
            self.view_offset < 1.0:
            self.view_offset = (d - 1.0)
        elif (d := self.specs[0][Attr.x]) > self.view_offset:
            self.view_offset = d
        else:
            self._keep_inview()
        client_size = lambda i: self.specs[i][Attr.x] + self.specs[i][Attr.w]
        if (s := (client_size(-1) - self.specs[0][Attr.x])) <= 1.0:
            self.view_offset = 0
            self.specs[0][Attr.x] = 0
            self.specs[0][Attr.w] /= s
            for i in range(1, len(self.specs)):
                self.specs[i][Attr.w] /= s
                self.specs[i][Attr.x] = client_size(i-1)    

    def configure(self, client: Window, screen_rect: ScreenRect) -> None:
        if not self._in_view(client):
            client.hide()
            return

        client_spec = self.specs[self.windows.index(client)]
        color = self.border_focus if client.has_focus else self.border_normal
        border = 0 if len(self.windows) == 1 and not self.border_on_single \
            else self.border_width
        width, height = screen_rect.width, screen_rect.height

        client.place(
            round((client_spec[0] - self.view_offset) * width),
            round(client_spec[1] * height),
            round(client_spec[2] * width - 1 * border),
            round(client_spec[3] * height - 1 * border),
            border,
            color,
            margin=self.margin,
        )
        client.unhide()

    def focus_first(self) -> Window | None:
        return self.windows[0] if len(self.windows) else None

    def focus_last(self) -> Window | None:
        return self.windows[-1] if len(self.windows) else None

    def focus_next(self, client: Window) -> Window | None:
        index = self.windows.index(client)
        if len(self.windows) - 1 > index:
            return self.windows[index + 1]
        self.way = Way.TORIGHT

    def focus_previous(self, client: Window) -> Window | None:
        index = self.windows.index(client)
        if index >= 1:
            self.current -= 1
            return self.windows[self.current]
        self.way = Way.TOLEFT

    @expose_command()
    def next(self) -> None:
        client = self.focus_next(self.windows[self.current])
        if client:
            self.group.focus(client, True)

    @expose_command()
    def previous(self) -> None:
        client = self.focus_previous(self.windows[self.current])
        if client:
            self.group.focus(client, True)
    
    @expose_command()
    def right(self) -> None:
        self.next()

    @expose_command()
    def left(self) -> None:
        self.previous()

    @expose_command()
    def grow_left(self):
        if not len(self.specs):
            return
        t = min(1, self.specs[self.current][2] + 0.01) - self.specs[self.current][2]
        if t > 0:
            for s in self.specs[: self.current + 1]:
                s[0] -= t
            self.specs[self.current][2] += t
            self._edge_fill()
            self.group.layout_all()

    @expose_command()
    def shrink_left(self):
        if not len(self.specs):
            return
        t = self.specs[self.current][2] - max(0.2, self.specs[self.current][2] - 0.01)
        if t > 0:
            for s in self.specs[ :self.current + 1]:
                s[0] += t
            self.specs[self.current][2] -= t
            self._edge_fill()
            self.group.layout_all()

    @expose_command()
    def grow_right(self):
        if not len(self.specs):
            return
        t = min(1, self.specs[self.current][2] + 0.01) - self.specs[self.current][2]
        if t > 0:
            for s in self.specs[self.current + 1: ]:
                s[0] += t
            self.specs[self.current][2] += t
            self._edge_fill()
            self.group.layout_all()

    @expose_command()
    def shrink_right(self):
        if not len(self.specs):
            return
        t = self.specs[self.current][2] - max(0.2, self.specs[self.current][2] - 0.01)
        if t > 0:
            for s in self.specs[self.current + 1: ]:
                s[0] -= t
            self.specs[self.current][2] -= t
            self._edge_fill()
            self.group.layout_all()

    def _swap(self, i, j):
        self.windows[i], self.windows[j] = self.windows[j], self.windows[i],

    @expose_command()
    def shuffle_left(self):
        if self.current >= 1:
            self._swap(self.current, self.current-1)
            self.group.layout_all()

    @expose_command()
    def shuffle_right(self):
        if self.current + 1 < len(self.specs):
            self._swap(self.current, self.current+1)
            self.group.layout_all()
