from __future__ import annotations
from typing import TYPE_CHECKING
from enum import Enum
from itertools import accumulate

from libqtile.command.base import expose_command
from libqtile.layout.base import Layout
from libqtile.backend.base import Window

from libqtile.log_utils import logger
from libqtile.config import ScreenRect
import tkinter as tk
from threading import Thread

if TYPE_CHECKING:
    from typing import Any, Generator, Self

    from libqtile.backend.base import Window
    from libqtile.config import ScreenRect
    from libqtile.group import _Group

class Way(Enum):
    TORIGHT = 1
    TOLEFT = 0

class Way(Enum):
    DECREASING = 0
    INCREASING = 1

class Direction(Enum):
    HORIZONTAL = 0
    VERTICAL = 1

class Attr:
    x = 0
    y = 1
    w = 2
    h = 3

class Get:
    coord = 0
    size = 1

class _Tail:
    def __init__ (self, **config):
        # index of the currently focused window within self.children
        self.current : int = 0 
        self.childrens : [_Tail | Window] = []
        self.specs : [[float]] = [] 
        self.dir = Direction.HORIZONTAL
        self.view_offset : float = 0.0
        self.client_threshold = 3
        self.size_ratio = 1 / self.client_threshold
        self.resize_amount = 0.01

    def focus(self, client: Window) -> _Tail | _VTail:
        for i,c in enumerate(self.childrens):
            if ((self._is_tail(i) and (r := c.focus(client))) or \
                    (c == client and (r := self))):
                self.current = i
                self._restore_invariants()
                return r
        return None
    
    def _is_tail(self, i):
        return isinstance(self.childrens[i], _VTail)

    def _client_extremum(self, i):
        return self.specs[i][Attr.x] + self.specs[i][Attr.w]

    def _tail_size(self):
        return self._client_extremum(-1) - self.specs[0][Attr.x]

    # called at any update of the sizes
    def _normalize(self) -> bool:
        tail_size = self._tail_size()
        if tail_size <= 1.0:
            self.view_offset = 0
            self.specs[0][Attr.x] = 0
            self.specs[0][Attr.w] /= tail_size
            for i in range(1, len(self.specs)):
                self.specs[i][Attr.w] /= tail_size
                self.specs[i][Attr.x] = self._client_extremum(i-1)    
            return True
        return False

    def _normalize_add(self):
        ct = (len(self.specs) - 1) / len(self.specs)
        off = self.view_offset
        for c in self.specs:
            c[Attr.x] = off
            c[Attr.w] *= ct
            off += c[Attr.w]

    def add_client(self, client: Window) -> None:
        # TODO: refactor
        if not len(self.childrens):
            self.childrens = [client]
            self.specs = [[0.0, 0.0, 1.0, 1.0]]
            return

        # if self.current < len(self.childrens) and self._is_tail(self.current):
        #    return self.childrens[self.current].add_client(client)

        is_last = self.current == len(self.specs)
        
        self.childrens.insert(self.current, client)
        if (k := len(self.specs) + 1) <= self.client_threshold:
            self.specs.insert(self.current, [0.0, 0.0, 1 / (k - 1), 1.0])
            self._normalize_add()
        else: #default behaviour
            cx = self._client_extremum(-1) if is_last else self.specs[self.current][Attr.x]
            self.specs.insert(self.current, [cx, 0.0, self.size_ratio, 1.0])
            for c in self.specs[self.current + 1: ]:
                c[Attr.x] += self.size_ratio
        if not is_last:
            self._update_view(self.current, self.current + 1)
        return
    
    def remove(self, client):
        for i in range(len(self.childrens)):
            if isinstance(self.childrens[i], _VTail):
                # TODO return self or client
                self.childrens[i].remove(client)
            elif self.childrens[i] == client:
                dw = self.specs[i][Attr.w]
                for s in self.specs[i+1:]:
                    s[Attr.x] -= dw
                del self.childrens[i], self.specs[i]
                return self

    def _update_view(self, i, j):
        def _closest(x, e, f):
            # pick y in [e, f] closest to x
            if e <= x <= f:
                return x
            return e if x < e else f

        # b <= d
        a,b = self._client_extremum(i) - 1, self.specs[i][Attr.x]
        c,d = self._client_extremum(j) - 1, self.specs[j][Attr.x]
        if c <= b:
            self.view_offset = _closest(self.view_offset, max(a, c), b) 
        else:
            self.view_offset = _closest(self.view_offset, a, b)

        """
        if c <= b <= d or a <= d <= b:
            self.view_offset = _closest(self.view_offset, max(a, c), min(b, d))
        else:
            self.view_offset = _closest(self.view_offset, a, b)
        """

    def _restore_view(self):
        # currently focused window is always fully on screen
        client_extremum = lambda i: self.specs[i][Attr.x] + self.specs[i][Attr.w]
        target = self.specs[self.current]
        if target[Attr.x] < self.view_offset:
            self.view_offset = target[Attr.x]
        elif (d := client_extremum(self.current)) > self.view_offset + 1.0:
            self.view_offset = d - 1.0

    def _restore_invariants(self):
        if not len(self.childrens) \
            or (self._client_extremum(-1) - self.specs[0][Attr.x]) < 1:
            self._normalize()

        # currently focused window is always fully on screen
        client_extremum = lambda i: self.specs[i][Attr.x] + self.specs[i][Attr.w]
        target = self.specs[self.current]
        if target[Attr.x] < self.view_offset:
            self.view_offset = target[Attr.x]
        elif (d := client_extremum(self.current)) > self.view_offset + 1.0:
            self.view_offset = d - 1.0

        # no blank margins
        if (d := (self.specs[-1][Attr.x] + self.specs[-1][Attr.w])) - \
            self.view_offset < 1.0:
            self.view_offset = (d - 1.0)
        elif (d := self.specs[0][Attr.x]) > self.view_offset:
            self.view_offset = d

    def _in_view(self, index: int) -> bool:
        target = self.specs[index]
        if (self.view_offset - target[2] < target[0] < self.view_offset + 1):
            return True
        return False

    def _collapse_tail(self, tail):
        index = self.childrens.index(tail)
        self.childrens[index] = tail.childrens[0]

    # TODO: no recursive, move to handler?
    def _find(self, client: Window) -> (_Tail,int):
        for i in range(len(self.childrens)):
            if isinstance(self.childrens[i], _Tail) and \
                (w := self.childrens[i]._find(client)):
                return w
            elif self.childrens[i] == client:
                return (self, i)

    def _get_current(self):
        p = self
        while isinstance(p.childrens[self.current], _Tail):
            p = p.childrens[self.current]
        return (p, p.current)

    '''
    def _traverse_from(self, i):
        p = self
        while not isinstance(p.childrens[i], Window):
            p = p.childrens[i]
            i = p.current
        return (p, i)
    '''

    def _traverse_from(self, i):
        if i < len(self.childrens):
            if not isinstance(p := p.childrens[i], Window):
                return p._traverse_from(p.current)
            return (p, p.current)

    def geometry_client(self, client, screen: ScreenRect) -> \
        tuple[int, int, int, int] | None:

        for i in range(len(self.childrens)):
            sub_screen = ScreenRect(
                x = round(screen.width * (self.specs[i][Attr.x] - self.view_offset)),
                y = screen.y,
                width = round(screen.width * self.specs[i][Attr.w]),
                height = screen.height
            )

            c = self.childrens[i]
            if self._is_tail(i) and (p := c.geometry_client(client, sub_screen)):
                return p
            elif c == client and self._in_view(i):
                return (
                    sub_screen.x,
                    sub_screen.y,
                    sub_screen.width,
                    sub_screen.height,
                )

    def focus_first(self) -> Window | None:
        if len(self.childrens) == 0:
            return None
        f = self.childrens[0]
        while self._is_tail(f):
            f = f.childrens[0]
        return f

    def focus_last(self) -> Window | None:
        if len(self.childrens) == 0:
            return None
        f = self.childrens[-1]
        while self._is_tail(f):
            f = f.childrens[-1]
        return f

    def _clients(self) -> Generator[Window, None, None]:
        for c in self.childrens:
            if isinstance(c, _Tail):
                yield from c._clients()
            yield c

    def _valid_current(self) -> bool:
        if 0 <= self.current < len(self.childrens):
            return True
        return False

    def focus_next(self, client: Window) -> Window | None:
        clients = list(self._clients())
        index = clients.index(client)
        if len(clients) - 1 > index:
            return clients[index + 1]

    def focus_previous(self, client: Window) -> Window | None:
        clients = list(self._clients())
        index = clients.index(client)
        if index >= 1:
            return clients[index - 1]

    # alt-tab
    def next(self):
        if isinstance(self.childrens[self.current], _Tail) \
            and (n := self.childrens[self.current].next()):
                return n
        if self.current + 1 < len(self.childrens):
            nc = self.childrens[self.current + 1]
            return nc.next() if isinstance(nc, _Tail) else nc

    # alt-shift-tab
    def previous(self):
        if isinstance(self.childrens[self.current], _Tail) \
            and (n := self.childrens[self.current].previous()):
                return n
        if self.current >= 1:
            nc = self.childrens[self.current - 1]
            return nc.previous() if isinstance(nc, _Tail) else nc

    # alt-l
    # TODO: not general
    def move_right(self):
        if self.current + 1 < len(self.childrens):
            return self, self.childrens[self.current + 1]
        if self.current + 1 == len(self.childrens):
            self.current += 1
        return self, None
    
    # alt-h
    # TODO: not general
    def move_left(self):
        if self.current >= 1:
            return self, self.childrens[self.current - 1]
        return self, None

    def grow_right(self):
        l = len(self.childrens)
        if l and self.current < l:
            delta = min(self.resize_amount, 1 - self.specs[self.current][Attr.w])
            if delta > 0:
                for c in self.specs[self.current + 1: ]:
                    c[Attr.x] += delta 
                self.specs[self.current][Attr.w] += delta
                self._restore_invariants()

    def grow_left(self):
        l = len(self.childrens)
        if l and self.current < l:
            delta = min(self.resize_amount, 1 - self.specs[self.current][Attr.w])
            if delta > 0:
                for c in self.specs[: self.current + 1]:
                    c[Attr.x] -= delta 
                self.specs[self.current][Attr.w] += delta
                self._restore_invariants()

    def shrink_right(self):
        l = len(self.childrens)
        if l and self.current < l:
            delta = min(self.specs[self.current][Attr.w] - 0.2, self.resize_amount)
            if delta > 0:
                for c in self.specs[self.current + 1: ]:
                    c[Attr.x] -= delta 
                self.specs[self.current][Attr.w] -= delta
                self._restore_invariants()

    def shrink_left(self):
        l = len(self.childrens)
        if l and self.current < l:
            delta = min(self.specs[self.current][Attr.w] - 0.2, self.resize_amount)
            if delta > 0:
                for c in self.specs[: self.current + 1]:
                    c[Attr.x] += delta 
                self.specs[self.current][Attr.w] -= delta
                self._restore_invariants()

    def _swap(self, i, j):
        self.childrens[i], self.childrens[j] = self.childrens[j], self.childrens[i]

    def shuffle_left(self):
        if self.current >= 1:
            self._swap(self.current, self.current-1)
            self.current -= 1
        return self

    def shuffle_right(self):
        if self.current + 1 < len(self.specs):
            self._swap(self.current, self.current+1)
            self.current += 1
        return self

    def shuffle_up(self):
        logger.warning(self.current)
        if self.current >= 1:
            p, q = self.childrens[self.current - 1], self.childrens[self.current]
            if not self._is_tail(self.current - 1):
                vt = self.childrens[self.current - 1] = _VTail(self)
                vt.add_client(p)
                vt.add_client(q)
                vt.focus(q)
                vt._update_view()
            else:
                vt = p
                vt.add_client(q)
                vt.focus(q)
                vt._update_view()
            dw = self.specs[self.current][Attr.w] 
            for s in self.specs[self.current + 1: ]:
                s[Attr.x] -= dw
            del self.childrens[self.current], self.specs[self.current]
            self._restore_invariants()
            return vt
        return self

    def shuffle_down(self):
        if self.current + 1 < len(self.specs):
            p, q = self.childrens[self.current], self.childrens[self.current + 1]
            if not self._is_tail(self.current + 1):
                vt = self.childrens[self.current + 1] = _VTail(self)
                vt.add_client(q)
                vt.add_client(p)
                vt.focus(p)
                vt._update_view()
            else:
                vt = q
                q.add_client(p)
                vt.focus(p)
                vt._update_view()
            dw = self.specs[self.current][Attr.w] 
            for s in self.specs[self.current+1: ]:
                s[Attr.x] -= dw
            del self.childrens[self.current], self.specs[self.current]
            self._restore_invariants()
            return vt
        return self

class _VTail:
    def __init__ (self, parent = None, **config):
        # index of the currently focused window within self.children
        self.current : int = 0 
        self.childrens : [_Tail | Window] = []
        self.specs : [tuple[float, float]] = [] 
        self.dir = Direction.VERTICAL
        self.view_offset : float = 0.0
        self.client_threshold = 2
        self.size_ratio = 1 / self.client_threshold
        self.resize_amount = 0.01
        self.parent = parent

    def focus(self, client: Window) -> _Tail | _VTail:
        for i,c in enumerate(self.childrens):
            if ((self._is_tail(i) and (r := c.focus(client))) or \
                    (c == client and (r := self))):
                self.current = i
                self._update_view()
                return r
        return None
    
    def _is_tail(self, i):
        return isinstance(self.childrens[i], _VTail)

    def _client_extremum(self, i):
        return self.specs[i][Get.coord] + self.specs[i][Get.size]

    def _tail_size(self):
        return self._client_extremum(-1) - self.specs[0][Get.coord]

    # called at any update of the sizes
    def _normalize(self) -> bool:
        tail_size = self._tail_size()
        if tail_size <= 1.0:
            self.view_offset = 0
            self.specs[0][Get.coord] = 0
            self.specs[0][Get.size] /= tail_size
            for i in range(1, len(self.specs)):
                self.specs[i][Get.coord] = self._client_extremum(i-1)    
                self.specs[i][Get.size] /= tail_size
            return True
        return False

    def _normalize_add(self):
        ct = (len(self.specs) - 1) / len(self.specs)
        off = self.view_offset
        for c in self.specs:
            c[Get.coord] = off
            c[Get.size] *= ct
            off += c[Get.size]

    def _update_view(self):
        flag = False
        # check if the removal left a window half-viewd
        for i in range(len(self.childrens)):
            c, s, o = *self.specs[i], self.view_offset
            if (c < o <= c + s) or (c <= o + 1 < c + s):
                flag = True
                break

        if self.current == 0:
            a, b = 0, min(len(self.specs), 3)
        elif self.current + 1 == (l := len(self.specs)):
            a, b = max(0, l - 3), l
        else:
            a = self.current - 1
            b = self.current + 2

        tail_size = sum(self.specs[i][Get.size] for i in range(a,b))
        if (self.specs[self.current][Get.coord] < self.view_offset) \
                or (self._client_extremum(self.current) > self.view_offset + 1.0) \
                or tail_size < 1 or flag:
            if self.current == 0:
                a, b = 0, min(len(self.specs), 3)
            elif self.current + 1 == (l := len(self.specs)):
                a, b = max(0, l - 3), l
            else:
                a = self.current - 1
                b = self.current + 2

            self.view_offset = self.specs[a][Get.coord]
            self.specs[a][Get.size] /= tail_size
            for i in range(a+1, b):
                self.specs[i][Get.coord] = self._client_extremum(i-1)    
                self.specs[i][Get.size] /= tail_size
            for c in self.specs[b: ]:
                c[Get.coord] +=  - tail_size + 1.0

    def _restore_view(self):
        if self.current == 0:
            a, b = 0, min(len(self.specs), 3)
        elif self.current + 1 == (l := len(self.specs)):
            a, b = max(0, l - 3), l
        else:
            a = self.current - 1
            b = self.current + 2

        tail_size = sum(self.specs[i][Get.size] for i in range(a,b))
        self.view_offset = self.specs[a][Get.coord]
        self.specs[a][Get.size] /= tail_size
        for i in range(a+1, b):
            self.specs[i][Get.coord] = self._client_extremum(i-1)    
            self.specs[i][Get.size] /= tail_size
        for c in self.specs[b: ]:
            c[Get.coord] += tail_size - 1.0

    def add_client(self, client: Window) -> None:
        # TODO: refactor
        if not len(self.childrens):
            self.childrens = [client]
            self.specs = [[0.0, 1.0]]
            return

        if self.current < len(self.childrens) and self._is_tail(self.current):
            return self.childrens[self.current].add_client(client)

        is_last = self.current == len(self.specs)
        
        self.childrens.insert(self.current, client)
        if (k := len(self.specs) + 1) <= self.client_threshold:
            self.specs.insert(self.current, [0.0, 1 / (k - 1)])
            self._normalize_add()
        else: #default behaviour
            cx = self._client_extremum(-1) if is_last else self.specs[self.current][Get.coord]
            self.specs.insert(self.current, [cx, self.size_ratio])
            for c in self.specs[self.current + 1: ]:
                c[Get.coord] += self.size_ratio
    
    def remove(self, client):
        for i in range(len(self.childrens)):
            if isinstance(self.childrens[i], _Tail):
                self.childrens[i]._remove(client)
            elif self.childrens[i] == client:
                dw = self.specs[i][Get.size]
                for s in self.specs[i+1:]:
                    s[Attr.x] -= dw
                del self.childrens[i], self.specs[i]
                if len(self.childrens) == 1:
                    self.parent._collapse_tail(self)
                    return self.childrens[0]
                else:
                    self.current = min(self.current, len(self.childrens) - 1)
                    self._restore_view()
                    return self.childrens[self.current]

    def _restore_invariants(self):
        if not len(self.childrens) \
            or (self._client_extremum(-1) - self.specs[0][Get.coord]) < 1:
            self._normalize()
        
        # currently focused window is always fully on screen
        client_extremum = lambda i: self.specs[i][Get.coord] + self.specs[i][Get.size]
        target = self.specs[self.current]
        if target[Attr.x] < self.view_offset:
            self.view_offset = target[Get.coord]
        elif (d := client_extremum(self.current)) > self.view_offset + 1.0:
            self.view_offset = d - 1.0

        # no blank margins
        if (d := (self.specs[-1][Get.coord] + self.specs[-1][Get.size])) - \
            self.view_offset < 1.0:
            self.view_offset = (d - 1.0)
        elif (d := self.specs[0][Get.coord]) > self.view_offset:
            self.view_offset = d

    def _in_view(self, index: int) -> bool:
        target = self.specs[index]
        if (self.view_offset - target[Get.size] + 0.001 < target[Get.coord] < self.view_offset + 1.0 - 0.001):
            return True
        return False

    # TODO: no recursive, move to handler?
    def _find(self, client: Window) -> (_Tail,int):
        for i in range(len(self.childrens)):
            if isinstance(self.childrens[i], _Tail) and \
                (w := self.childrens[i]._find(client)):
                return w
            elif self.childrens[i] == client:
                return (self, i)

    def _current_tail(self):
        p = self
        while isinstance(p.childrens[self.current], _Tail):
            p = p.childrens[self.current]
        return (p, p.current)

    def geometry_client(self, client, screen: ScreenRect) -> \
        tuple[int, int, int, int] | None:
        
        for i in range(len(self.childrens)):
            sub_screen = ScreenRect(
                x = screen.x,
                y = round(screen.height * (self.specs[i][Get.coord] - self.view_offset)),
                width = screen.width,
                height = round(screen.height * self.specs[i][Get.size])
            )

            c = self.childrens[i]
            if self._is_tail(i) and (p := c.geometry_client(client, sub_screen)):
                return p
            elif c == client and self._in_view(i):
                return (
                    sub_screen.x,
                    sub_screen.y,
                    sub_screen.width,
                    sub_screen.height,
                )

    def focus_first(self) -> Window | None:
        if len(self.childrens) == 0:
            return None
        f = self.childrens[0]
        while self._is_tail(f):
            f = f.childrens[0]
        return f

    def focus_last(self) -> Window | None:
        if len(self.childrens) == 0:
            return None
        f = self.childrens[-1]
        while self._is_tail(f):
            f = f.childrens[-1]
        return f

    def _clients(self) -> Generator[Window, None, None]:
        for c in self.childrens:
            if isinstance(c, _Tail):
                yield from c._clients()
            yield c

    def _valid_current(self) -> bool:
        if 0 <= self.current < len(self.childrens):
            return True
        return False

    def focus_next(self, client: Window) -> Window | None:
        clients = list(self._clients())
        index = clients.index(client)
        if len(clients) - 1 > index:
            return clients[index + 1]
        self.way = Way.DECREASING

    def focus_previous(self, client: Window) -> Window | None:
        clients = list(self._clients())
        index = clients.index(client)
        if index >= 1:
            return clients[index - 1]
        self.way = Way.INCREASING

    # alt-tab
    def next(self):
        if isinstance(self.childrens[self.current], _Tail) \
            and (n := self.childrens[self.current].next()):
                return n
        if self.current + 1 < len(self.childrens):
            nc = self.childrens[self.current + 1]
            return nc.next() if isinstance(nc, _Tail) else nc

    # alt-shift-tab
    def previous(self):
        if isinstance(self.childrens[self.current], _Tail) \
            and (n := self.childrens[self.current].previous()):
                return n
        if self.current >= 1:
            nc = self.childrens[self.current - 1]
            return nc.previous() if isinstance(nc, _Tail) else nc

    # TODO: not general
    def move_down(self):
        if self.current + 1 < len(self.childrens):
            return self, self.childrens[self.current + 1]
        if self.current + 1 == len(self.childrens):
            self.current += 1
        return self, None
    
    # alt-h
    # TODO: not general
    def move_up(self):
        if self.current >= 1:
            return self, self.childrens[self.current - 1]
        return self, None

    def grow_up(self):
        l = len(self.childrens)
        if l > 0 and self.current < l:
            delta = min(self.resize_amount, 1 - self.specs[self.current][Get.size])
            if delta > 0:
                for c in self.specs[self.current + 1: ]:
                    c[Get.coord] += delta 
                self.specs[self.current][Get.size] += delta
                self._update_view()

    def grow_down(self):
        l = len(self.childrens)
        if l > 0 and self.current < l:
            delta = min(self.resize_amount, 1 - self.specs[self.current][Get.size])
            if delta > 0:
                for c in self.specs[: self.current + 1]:
                    c[Get.coord] -= delta 
                self.specs[self.current][Get.size] += delta
                self._update_view()

    def shrink_up(self):
        l = len(self.childrens)
        if l > 0 and self.current < l:
            delta = min(self.specs[self.current][Get.size] - 0.2, self.resize_amount)
            if delta > 0:
                for c in self.specs[self.current + 1: ]:
                    c[Get.coord] -= delta 
                self.specs[self.current][Get.size] -= delta
                self._update_view()

    def shrink_down(self):
        l = len(self.childrens)
        if l > 0 and self.current < l:
            delta = min(self.specs[self.current][Get.size] - 0.2, self.resize_amount)
            if delta > 0:
                for c in self.specs[: self.current + 1]:
                    c[Get.coord] += delta 
                self.specs[self.current][Get.size] -= delta
                self._update_view()

    def _swap(self, i, j):
        self.childrens[i], self.childrens[j] = self.childrens[j], self.childrens[i]

    def shuffle_up(self):
        if self.current >= 1:
            self._swap(self.current, self.current-1)
            self.current -= 1
        return self

    def shuffle_down(self):
        if self.current + 1 < len(self.specs):
            self._swap(self.current, self.current+1)
            self.current += 1
        return self

    def shuffle_left(self):
        # TODO: unsafe vs interface insert
        p = self.childrens[self.current]
        self.parent.add_client(p)
        self.remove(p)
        return self.parent

    # drag-left
    def shuffle_right(self):
        # TODO: unsafe vs interface insert
        p = self.childrens[self.current]
        self.parent.current += 1
        self.parent.add_client(p)
        self.remove(p)
        return self.parent

class qTail(Layout):
    def __init__ (self, **config):
        Layout.__init__(self, **config)
        # self.add_defaults(Bsp.defaults) # finally
        self.margin = config['margin']
        self.border_focus = "#FF0000"
        self.border_normal = "#DDEEDD"
        self.border_on_single = False
        self.border_width = 2
        self.size_ratio = 1 / 3
        self.root = _Tail()
        self.current = self.root

    def clone(self, group: _Group) -> Self:
        c = Layout.clone(self, group)
        c.margin = self.margin
        c.border_focus = "#FF0000"
        c.border_normal = "#DDEEDD"
        c.border_on_single = False
        c.border_width = 2
        c.size_ratio = 1 / 3
        c.root = _Tail()
        c.current = c.root
        return c

    def _traverse(self, tail, i):
        while True:
            i = min(max(0, i), len(tail.childrens) - 1)
            c = tail.childrens[i]
            if not isinstance(c, Window):
                i = tail.current
                tail = c
            else:
                return tail, c

    def get_windows(self):
        return self.windows

    def focus(self, client: Window) -> None:
        # TODO: move logic here
        self.current = self.root.focus(client)

    def add_client(self, client: Window) -> None:
        self.current.add_client(client)

    def remove(self, client):
        # TODO handle empty root
        self.current = self.root.remove(client)

    def configure(self, client: Window, screen_rect: ScreenRect) -> None:
        color = self.border_focus if client.has_focus else self.border_normal
        border = 0 if len(self.root.childrens) == 1 and not self.border_on_single \
            else self.border_width
        
        if (tp := self.root.geometry_client(client, screen_rect)):
            cx, cy, cw, ch = tp
            client.place(
                cx, 
                cy, 
                cw - 2*border,
                ch - 2*border,
                2,
                color,
                margin=self.margin,
            )
            client.unhide()
        else:
            client.hide()

    def focus_first(self) -> Window | None:
        return self.root.focus_first()

    def focus_last(self) -> Window | None:
        return self.root.focus_last()

    def focus_next(self, client: Window) -> Window | None:
        return self.root.focus_next()

    def focus_previous(self, client: Window) -> Window | None:
        return self.root.focus_previous()

    @expose_command()
    def next(self) -> None:
        current, client = self.root.next()
        if client:
            self.group.focus(client, True)
            self.current = current

    @expose_command()
    def previous(self) -> None:
        current, client = self.root.next()
        if client:
            self.group.focus(client, True)
            self.current = current
    
    @expose_command()
    def right(self) -> None:
        self.next()

    @expose_command()
    def left(self) -> None:
        self.previous()

    @expose_command()
    def move_right(self) -> None:
        tail = self.current if self.current.dir == Direction.HORIZONTAL \
                else self.current.parent
        if tail.current + 1 >= len(tail.childrens):
            tail.current = len(tail.childrens)
            self.current = tail
            return
        self.current, client = self._traverse(tail, i = tail.current + 1)
        if client:
            self.group.focus(client, True)

    @expose_command()
    def move_left(self) -> None:
        tail = self.current if self.current.dir == Direction.HORIZONTAL \
                else self.current.parent
        if tail.current == 0:
            self.current = tail
            return
        self.current, client = self._traverse(tail, i = tail.current - 1)
        if client:
            self.group.focus(client, True)
        
    @expose_command()
    def move_up(self) -> None:
        self.current, client = self.current.move_up()
        if client:
            self.group.focus(client, True)

    @expose_command()
    def move_down(self) -> None:
        self.current, client = self.current.move_down()
        if client:
            self.group.focus(client, True)

    @expose_command()
    def grow_left(self):
        self.root.grow_left()
        self.group.layout_all()

    @expose_command()
    def shrink_left(self):
        self.root.shrink_left()
        self.group.layout_all()

    @expose_command()
    def grow_right(self):
        self.root.grow_right()
        self.group.layout_all()

    @expose_command()
    def shrink_right(self):
        self.root.shrink_right()
        self.group.layout_all()

    @expose_command()
    def grow_up(self):
        self.current.grow_up()
        self.group.layout_all()

    @expose_command()
    def shrink_up(self):
        self.current.shrink_up()
        self.group.layout_all()

    @expose_command()
    def grow_down(self):
        self.current.grow_down()
        self.group.layout_all()

    @expose_command()
    def shrink_down(self):
        self.current.shrink_down()
        self.group.layout_all()

    @expose_command()
    def shuffle_left(self):
        self.current = self.current.shuffle_left()
        self.group.layout_all()

    @expose_command()
    def shuffle_right(self):
        self.current = self.current.shuffle_right()
        self.group.layout_all()

    @expose_command()
    def shuffle_down(self):
        self.current = self.current.shuffle_down()
        self.group.layout_all()

    @expose_command()
    def shuffle_up(self):
        self.current = self.current.shuffle_up()
        self.group.layout_all()
