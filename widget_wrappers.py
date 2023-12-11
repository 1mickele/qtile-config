from libqtile.widget import base
from libqtile.lazy import lazy

class Tester(base._TextBox):
    def __init__ (self, **config):
        base._TextBox.__init__(self, "", **config)
        self.add_callbacks({
            "Button1": lambda: self.update_text(True),
            "Button3": lambda: self.update_text(False),
            "Button2": self.update_textl,
        })

    def _configure(self, qtile, bar):
        base._TextBox._configure(self, qtile, bar)
        self.text = "!"

    def update_text(self, expand):
        if expand:
            self.text += 'Q'
        else:
            self.text = self.text[0:len(self.text)-1]

    def update_textl(self):
        self.text = str(self.length)

from libqtile.widget import prompt

class TesterPrompt(prompt.Prompt):
    def __init__ (self, **config):
        self.text2 = ""
        prompt.Prompt.__init__(self, bell_style="visual", **config)
        self.add_callbacks({
            "Button1": lambda: self.start_input("aa", 
                lambda s: self.timeout_add(0.5, lambda : self.compute_length(s))),
            "Button3": lambda: self.compute_length(self.text2)
        })
        self.text = "!!!!"

    def compute_length(self, te):
        self.text2 = self.text = te
        self.text = str(super().calculate_length())

import random
import math

# Almost done
class TextWrapperPrototype(base._TextBox):
    def __init__ (self, t, **config):
        base._TextBox.__init__(self, t, scroll = False, **config)
        self.block = 30.0
        self.add_callbacks({
            "Button5": self.update
        })

    def _configure(self, qtile, bar):
        base._TextBox._configure(self, qtile, bar)

    def calculate_length(self):
        l = super().calculate_length()
        t = (int(l / self.block) + 1) * self.block
        self._scroll_offset = -((t - l) / 2.0) 
        return t

    def update(self):
        # super().timeout_add(0.1, self.update)
        self.text = "".join([str(random.randint(0, 9)) for _ in range(10)])

def MyWrapper(*, Widget, **configs):
    def average(n: int):
        k: int = 0
        xs = [0] * n 
        def inner(x):
            nonlocal xs, k
            xs[k % n] = x
            k = (k + 1) % n + (n if (k + 1) >= n else 0)
            return sum(xs) / min(k, n)
        return inner

    rbinc = lambda x, l, c: round((x - c) / l) * l + c
    gbinc = lambda x, l, c: (int((x - c) / l) + 1) * l + c

    def init (self, *, tollerance = 30, precision = 3, 
            reset_threshold = 40, **configs):
        Widget.__init__(self, **configs)
        self.tollerance = tollerance
        self.precision = precision
        self.reset_threshold = reset_threshold

        self.average_offset = average(50)
        self.prev_length = 0
        self.prev_offset = 0
    
    def calculate_length(self):
        l = super(Widget, self).calculate_length()
        t = gbinc(l, self.tollerance, self.prev_length)
        if self.prev_length != t:
            self.prev_length = t + self.tollerance / 2.0

        n = (t - l) / 2.0
        if (k := abs(self.prev_offset - (s := self.average_offset(n)))) > self.precision:
            if k > self.reset_threshold:
                self.average_offset = average(50)
                self.average_offset(s)
            self.prev_offset += -math.copysign(1, self.prev_offset - s)
        self._scroll_offset = -self.prev_offset
        return t

    def _configure(self, qtile, bar):
        Widget._configure(self, qtile, bar)

    WrappedWidget = type('My' + Widget.__name__, (Widget, object), {
        "__init__": init,
        "_configure": _configure,
        "calculate_length": calculate_length
    })

    return WrappedWidget(**configs)

def MyCenteredWrapper(*, Widget, **configs):
    gbinc = lambda x, l, c: (int((x - c) / l) + 1) * l + c

    def init (self, *, tollerance = 30, **configs):
        Widget.__init__(self, **configs)
        self.tollerance = tollerance

        self.prev_length = 0
    
    def calculate_length(self):
        l = super(Widget, self).calculate_length()
        t = gbinc(l, self.tollerance, self.prev_length)
        if self.prev_length != t:
            self.prev_length = t + self.tollerance / 2.0
        self._scroll_offset = -(t - l) / 2.0

        return t

    def _configure(self, qtile, bar):
        Widget._configure(self, qtile, bar)

    WrappedWidget = type('MyCentered' + Widget.__name__, (Widget, object), {
        "__init__": init,
        "_configure": _configure,
        "calculate_length": calculate_length
    })

    return WrappedWidget(**configs)
