from pathlib import Path



class PrefixBundlerBase:
    # a prefix-bundler takes a prefix (todo, fix arguments / parametrization / api)
    # and turns this into something a kernel can consume
    def __init__(self, addon, kernel_name):
        self.addon = addon
        self.cwd = addon.cwd
        self.copy_one = addon.copy_one
        self.prefix = addon.prefix
        self.kernel_name = kernel_name
        self.static_dir = addon.static_dir
        self.packages_dir = Path(self.static_dir) / "kernel_packages"
        self.kernel_dir = addon.static_dir / "kernels"/ kernel_name
    
    def build(self):
        raise NotImplementedError("build method must be implemented by subclass")
