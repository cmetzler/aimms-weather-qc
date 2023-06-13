import argparse
import sys

from gooey import *
from gooey.python_bindings.gooey_decorator import IGNORE_COMMAND


def is_gooey_wrapped():
    return IGNORE_COMMAND in sys.argv


wrapped_args = is_gooey_wrapped()


class UnbufferedStream:
    # https://stackoverflow.com/questions/107705/disable-output-buffering

    def __init__(self, stream, force_newline=False):
        self.stream = stream
        self.force_newline = force_newline

    def write(self, data):
        data = self.format_string(data)
        self.stream.write(data)
        self.stream.flush()

    def writelines(self, datas):
        datas = (self.format_string(data) for data in datas)
        self.stream.writelines(datas)
        self.stream.flush()

    def format_string(self, data):
        if self.force_newline:
            data = data.lstrip()
            if data and not data.endswith('\n'):
                data += '\n'
        return data

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


class StoreMultiFileArgument(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if wrapped_args:
            s, = values
            values = s.split(';')
        setattr(namespace, self.dest, values)


def gooey_on_empty_args(ignore_gooey=False, *args, **kwargs):
    def wrap_outer(fn, *w_args, **w_kwargs):
        def wrap_inner():
            return fn(*w_args, **w_kwargs)
        return wrap_inner

    if ignore_gooey:
        return wrap_outer
    elif sys.argv[1:]:
        if is_gooey_wrapped():
            sys.argv.remove(IGNORE_COMMAND)
        return wrap_outer

    return Gooey(*args, **kwargs)


sys.stdout = UnbufferedStream(sys.stdout)
sys.stderr = UnbufferedStream(sys.stderr)
tqdm_stream = UnbufferedStream(sys.stdout, force_newline=is_gooey_wrapped())