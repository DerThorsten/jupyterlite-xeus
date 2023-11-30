"""a JupyterLite addon for creating the env for xeus-python"""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from jupyterlite_core.addons.federated_extensions import FederatedExtensionAddon
from jupyterlite_core.constants import (
    FEDERATED_EXTENSIONS,
    JUPYTERLITE_JSON,
    LAB_EXTENSIONS,
    SHARE_LABEXTENSIONS,
    UTF8,
)
from traitlets import List, Unicode


EXTENSION_NAME = "xeus-python-kernel"
STATIC_DIR = Path("@jupyterlite") / EXTENSION_NAME / "static"



class PackagesList(List):
    def from_string(self, s):
        return s.split(",")


class XeusKernelLoaderAddon(FederatedExtensionAddon):
    __all__ = ["post_build"]


    environment_file = Unicode(
        "environment.yml",
        config=True,
        description='The path to the environment file. Defaults to "environment.yml"',
    )

    prefix = Unicode(
        "",
        config=True,
        description='The path to the wasm prefix',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cwd = TemporaryDirectory()

    def post_build(self, manager):
        print("\n\n\n")
        print("post_build", manager)

        if self.prefix:
            yield from self.copy_kernels_from_prefix(manager)



    def copy_kernels_from_prefix(self, manager):
        print("the prefix",self.prefix)
        static_dir = self.output_extensions / STATIC_DIR
        
        if not os.path.exists(self.prefix) or not os.path.isdir(self.prefix):
            raise ValueError(f"Prefix {self.prefix} does not exist or is not a directory")

        kernel_spec_path = Path(self.prefix) / "share" / "jupyter" / "kernels"

        
        all_kernels = []
        # find all folders in the kernelspec path
        for kernel_dir in kernel_spec_path.iterdir():
            # ignore  all special files starting with .
            if kernel_dir.name.startswith("."):
                continue
            
            # # check if it contains a hook.py file
            # if (kernel_dir / "hook.py").exists():
            #     # execute the hook.py file
            #     print("hook.py exists")
            #     exec(open(kernel_dir / "hook.py").read())
                
            all_kernels.append(kernel_dir.name)
            # copy the kernel to the static dir
            yield from self.copy_kernel(kernel_dir, static_dir)
        
        # serialize all_kernels to temp file


        kernel_file = Path(self.cwd.name) / "kernels.json"
        kernel_file.write_text(json.dumps(all_kernels), **UTF8)
        yield dict(
            name=f"xeus:copy:kernels.json",
            actions=[(self.copy_one, [kernel_file, static_dir / "kernels.json" ])],
        )




    def copy_kernel(self, kernel_dir, static_dir):

        kernel_spec = json.loads((kernel_dir / "kernel.json").read_text(**UTF8))
        
        # print nice
        print(json.dumps(kernel_spec, indent=4))

        yield dict(
            name=f"xeus:copy_kernel:{kernel_dir.name}",
            actions=[(self.copy_one, [kernel_dir, static_dir / "kernels"/ kernel_dir.name ])],
        )
    

    # it is a bit unfortunate that we have to hard code 
    # some kernel specifics, but atm this is the easiest way
    # to get it working

    