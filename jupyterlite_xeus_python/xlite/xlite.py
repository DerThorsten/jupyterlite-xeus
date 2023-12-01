from pathlib import Path

class XLiteBuilderBase:
    def __init__(self, addon,kernel_name, static_dir):
        self.addon = addon
        self.kernel_name = kernel_name
        self.static_dir = static_dir
        self.packages_dir = Path(self.static_dir) / "kernel_packages"

    
    def build(self, kernel_dir):
        yield 
