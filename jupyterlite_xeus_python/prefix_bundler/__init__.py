from .prefix_bundler_base import PrefixBundlerBase
from .empack_bundler import EmpackBundler

# register
prefix_bundler_registry = {
    "empack": EmpackBundler,
    "default": PrefixBundlerBase
}
def get_prefix_bundler(name):
    if name is None:
        name = "default"
    return prefix_bundler_registry[name] 