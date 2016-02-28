from functools import wraps
import cPickle

def pickled(func):
    fn = func.func_name + '.pickle'

    @wraps(func)
    def wrapper(*args, **kw):
        try:
            with open(fn, 'r') as f:
                result = cPickle.load(f)
                return result
        except IOError as e:
            if e.errno != 2:
                raise

            result = func(*args, **kw)
            with open(fn, 'w') as f:
                cPickle.dump(result, f)
            return result

    return wrapper
