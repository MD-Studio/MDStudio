import os

from mdstudio.component.session import ComponentSession

try:
    input = raw_input
except NameError:
    pass

class CLIComponent(ComponentSession):
    pass