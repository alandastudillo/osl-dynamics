import inspect
import logging
from functools import wraps
from time import time

from taser.helpers.misc import time_axis_first


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print(f"{f.__name__!r} took: {te - ts:2.4f} sec")
        return result

    return wrap


def doublewrap(f):
    """
    a decorator decorator, allowing the decorator to be used as:
    @decorator(with, arguments, and=kwargs)
    or
    @decorator
    """

    @wraps(f)
    def new_dec(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # actual decorated function
            return f(args[0])
        else:
            # decorator arguments
            return lambda realf: f(realf, *args, **kwargs)

    return new_dec


@doublewrap
def transpose(f, *arguments):
    try:
        iter(arguments)
    except TypeError:
        arguments = [arguments]
    finally:
        positional_arguments = [a for a in arguments if isinstance(a, int)]
        keyword_arguments = [a for a in arguments if isinstance(a, str)]

    @wraps(f)
    def wrap(*args, **kwargs):
        args = [*args]
        for i in positional_arguments:
            try:
                args[i], transposed = time_axis_first(args[i])
                if transposed:
                    logging.warning(
                        f"Argument {i}: assuming longer axis to be time and transposing."
                    )
            except IndexError:
                logging.debug(f"Positional argument {i} not in args.")
        for k in keyword_arguments:
            try:
                kwargs[k], transposed = time_axis_first(kwargs[k])
                if transposed:
                    logging.warning(
                        f"Argument {k}: assuming longer axis to be time and transposing."
                    )
            except KeyError:
                logging.debug(f"Argument {k} not found in kwargs.")

        return f(*args, **kwargs)

    return wrap


def auto_repr(func):
    @wraps(func)
    def wrapper_function(me, *args, **kwargs):
        arg_dict = {}
        params = inspect.signature(me.__class__).parameters

        sig_dict = params.items()
        for i, (key, val) in enumerate(params.items()):
            if i < len(args):
                arg_dict[key] = args[i]
            if i >= len(args):
                if key in kwargs:
                    arg_dict[key] = kwargs[key]
                elif key in params:
                    arg_dict[key] = params[key].default

        me.__arg_dict = arg_dict

        def __repr__(self):
            return (
                self.__class__.__name__
                + "("
                + ", ".join(
                    "=".join(
                        [
                            item[0],
                            str(item[1])
                            if not isinstance(item[1], str)
                            else "'" + item[1] + "'",
                        ]
                    )
                    for item in self.__arg_dict.items()
                )
                + ")"
            )

        setattr(me.__class__, "__repr__", __repr__)

        func(me, *args, **kwargs)

    return wrapper_function
