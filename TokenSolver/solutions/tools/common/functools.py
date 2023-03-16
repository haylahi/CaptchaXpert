def get_func_name(func):
    try:
        fn_name = func.__name__
    except AttributeError:
        try:
            fn_name = func.__class__.__name__
        except AttributeError:
            fn_name = 'func'
    return fn_name

