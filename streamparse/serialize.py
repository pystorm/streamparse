import pickle
import zlib
from base64 import b64encode, b64decode


def encode(obj):
    pickled = pickle.dumps(obj)
    compressed = zlib.compress(pickled)

    # Ensures that we use the smallest possible form.
    if len(compressed) < len(pickled):
        label = '_pyobj_zlib'
        content = compressed
    else:
        label = '_pyobj'
        content = pickled

    return {label: b64encode(content)}


def decode(dct):
    if '_pyobj_zlib' in dct:
        return pickle.loads(zlib.decompress(b64decode(dct['_pyobj_zlib'])))
    elif '_pyobj' in dct:
        return pickle.loads(b64decode(dct['_pyobj']))
    else:
        return dct
