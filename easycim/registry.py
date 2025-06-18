CONVERTER_FUNC_REGISTRY = {}
 
def register_converter(cls):
    def decorator(func):
        CONVERTER_FUNC_REGISTRY[cls] = func
        return func
    return decorator