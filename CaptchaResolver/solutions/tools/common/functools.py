import copy
import os
import sys
try:
    from termcolor import colored
except ImportError:
    pass


def verbose(func):
    """
    Decorate any function so that when you parse --verbose in cli, it will show function info
    Limitations::
        Raise and error if object is static method
    Possible *argv::
        0: No verbose
        1: only func name
        2: func name with args
        3: func name with keyword arguments too
    :param func: function to run
    :return: response of func

    """

    def wrapper(*args, **kwargs):
        if '--verbose' in sys.argv:
            if hasattr(sys.modules[__name__], 'colored'):
                _prefix = colored(f"[Verbose]", attrs=['bold', 'dark', 'underline'])
            else:
                _prefix = '[Verbose]'
            if isinstance(func, staticmethod):
                raise Exception("Not implemented, try to verbose first then staticmethod")
            level = int(sys.argv[sys.argv.index('--verbose') + 1])
            if level != 0:
                if len(args) >= 1 and isinstance(args[0], object):
                    if func.__name__ == "__init__":
                        return func(*args, **kwargs)
                    print(f"{_prefix} Calling `{args[0].__class__.__name__}().{func.__name__}()`"
                          f" {f'with args as {args}' if level > 1 else ''} {f'and kwargs as {kwargs}' if level > 2 else ''}")
                else:
                    print(f"{_prefix} Calling `{func.__name__}()` "
                          f"{f'with args as {args}' if level > 1 else ''} {f'and kwargs as {kwargs}' if level > 2 else ''}")

            res = func(*args, **kwargs)
            if level != 0:
                print(f"{_prefix} {args[0].__class__.__name__ if len(args) >= 1 and isinstance(args[0], object) else ''}()."
                      f"{func.__name__}() returned", res)

            return res
        else:
            return func(*args, **kwargs)

    return wrapper


def get_modules(root_dir, exclude_dirs: tuple or list = (), exclude_modules: tuple or list = (), path_type="abs",
                relative_dir=os.getcwd()) -> list:
    """
    Get all modules from target project tree
    :param root_dir: project directory
    :param exclude_dirs: skip mentioned directories
    :param exclude_modules: skip mentioned modules
    :param path_type: type of path needed, i.e `abs` or `relative` or `name`
    :param relative_dir: if path_type is relative then relative_dir can be useful
    :return: list of paths
    """
    modules = []
    for name in os.listdir(root_dir):
        path = os.path.join(root_dir, name)
        if os.path.isdir(path):
            if len([x for x in exclude_dirs if x == name]) > 0:
                continue
            modules.extend(get_modules(path, exclude_dirs, exclude_modules, path_type, relative_dir))
        elif name.endswith('.py'):
            if len([x for x in exclude_modules if x == name]) > 0:
                continue
            if path_type == "abs":
                modules.append(os.path.abspath(os.path.join(root_dir, name)))
            elif path_type == "relative":
                modules.append(os.path.join(root_dir, name).replace('/', '\\').replace(relative_dir, '')[1:])
            elif path_type == 'name':
                modules.append(name)

    return modules


def decorate_module(module_name):
    print(f"@Decorating: {module_name} with verbose wrapper")
    _module = sys.modules.get(module_name)
    if _module is None:
        print(f"Failed to decorate {module_name} with verbose wrapper, NoSuchModuleFoundInSysModules")
        return False
    else:
        module_dict = _module.__dict__

    for func in copy.copy(module_dict).values():
        if callable(func):
            if isinstance(func, type):
                for n, v in func.__dict__.copy().items():
                    if callable(v) and not n.startswith('__'):
                        setattr(func, n, verbose(v))
            else:
                if func.__name__ == 'verbose':
                    continue
                module_dict[func.__name__] = verbose(func)
    print(f"\nDecorated all methods and functions in {module_name} with verbose wrapper")


def decorate_mytools():
    if '--verbose' in sys.argv:
        ex_dirs = ['venv', '__pycache__']
        __dir_path__ = os.path.dirname(os.path.dirname(__file__))
        __dir_name__ = os.path.basename(__dir_path__)
        __all_modules__ = [x.replace('\\', '.') for x in get_modules(__dir_path__, exclude_dirs=ex_dirs
                                                                     , exclude_modules=['functools.py'], path_type='relative'
                                                                     , relative_dir=os.path.dirname(os.path.dirname(__file__)))]
        __all_modules__ = [f"{__dir_name__}.{x.replace('.py', '')}" for x in __all_modules__]
        for m in __all_modules__:
            decorate_module(m)
        return True
    return False


def decorate_all_modulues():
    modules = sys.modules.keys()
    for m in modules:
        if 'mytools' not in m and 'CryptoScrape' not in m and 'CaptchaSolutions' not in m:
            continue
        if 'functools' in m:
            continue
        try:
            decorate_module(m)
        except:
            print(m, "failed")


if __name__ == '__main__':
    decorate_all_modulues()