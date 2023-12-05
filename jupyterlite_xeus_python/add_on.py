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

from .prefix_bundler import get_prefix_bundler
from .create_conda_env import create_conda_env_from_yaml

EXTENSION_NAME = "xeus-python-kernel"
STATIC_DIR = Path("@jupyterlite") / EXTENSION_NAME / "static"


def is_kernel_dir(path):
    # hack to remove xpython-raw
    if "xpython-raw" in path.name:
        return False
    return (path / "kernel.json").exists()


class PackagesList(List):
    def from_string(self, s):
        return s.split(",")




class XeusAddon(FederatedExtensionAddon):
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

        # from prefix has higher priority than from environment file
        if self.prefix:
            # from existing prefix
            yield from self.copy_kernels_from_prefix(manager, prefix=self.prefix)
        else:
            # from environment file
            
            yield from self.create_and_copy_from_env(manager,  environment_file=self.environment_file)
    
    def create_and_copy_from_env(self, manager, environment_file):
        print("environment_file", environment_file)
        # read the environment file
        root_prefix = Path(self.cwd.name) / "env"
        env_name = "xeus-python"
        env_prefix = root_prefix / "envs" / env_name
        self.prefix = str(env_prefix)
        create_conda_env_from_yaml(
            env_name=env_name,
            root_prefix=root_prefix,
            env_file=environment_file,
        )
        yield from self.copy_kernels_from_prefix(manager, prefix=env_prefix)
       
        

    def copy_kernels_from_prefix(self, manager, prefix):
        static_dir = self.output_extensions / STATIC_DIR
        
        if not os.path.exists(prefix) or not os.path.isdir(prefix):
            raise ValueError(f"Prefix {prefix} does not exist or is not a directory")

        kernel_spec_path = Path(prefix) / "share" / "jupyter" / "kernels"


        all_kernels = []
        # find all folders in the kernelspec path
        for kernel_dir in kernel_spec_path.iterdir():
            print("considering kernel_dir", kernel_dir, is_kernel_dir(kernel_dir))
            if is_kernel_dir(kernel_dir):      

                all_kernels.append(kernel_dir.name)

                # take care of each kernel
                yield from self.copy_kernel(kernel_dir, static_dir)

        # write the kernels.json file
        kernel_file = Path(self.cwd.name) / "kernels.json"
        kernel_file.write_text(json.dumps(all_kernels), **UTF8)
        yield dict(
            name=f"xeus:copy:kernels.json",
            actions=[(self.copy_one, [kernel_file, static_dir /"kernels"/ "kernels.json" ])],
        )




    def copy_kernel(self, kernel_dir, static_dir):
        kernel_spec = json.loads((kernel_dir / "kernel.json").read_text(**UTF8))

        
        # copy the kernels content:
        # from: share/jupyter/kernels/<kernel_name> 
        # to: static/kernels/<kernel_name>
        #  This is must at least be:
        #  * the *.wasm  and *js files of the kernel (ie emscripten generated files)
        #  * the kernel.json file (with the correct path to the wasm file in the metadata)
        #  * the 2 logo files (logo-32x32.png and logo-64x64.png)
        yield dict(
            name=f"xeus:copy_kernel:{kernel_dir.name}",
            actions=[(self.copy_one, [kernel_dir, static_dir / "kernels"/ kernel_dir.name ])],
        )

        # this part is a bit more complicated:
        # Some kernels expect certain files to be at a certain places on the hard drive.
        # Ie python (even pure python without additional packages) expects to find certail *.py
        # files in a dir like $PREFIX/lib/python3.11/... .
        # Since the kernels run in the browser we need a way to take the needed files from the
        # $PREFIX of the emscripten-32 wasm env, bundle them into smth like  tar.gz file(s) and
        # copy them to the static/kernels/<kernel_name> dir.
        #
        # this concept of taking a prefix and turning it into something the kernels 
        # can consume is called a "bundler" in this context. 
        # At the moment, only xpython needs such a bundler, but this is likely to change in the future.
        # therefore we do the following. Each kernel can specify which bundler it needs in its kernel.json file.
        # If no bundler is specified, we assume that the default bundler is used (which does nothing atm).

        language = kernel_spec["language"].lower()
        prefix_bundler_name = kernel_spec["metadata"].get("prefix_bundler", None)
        prefix_bundler_kwargs = kernel_spec["metadata"].get("prefix_bundler_kwargs", dict())


        # THIS WILL BE REMOVED ONCE THE NEXT VERSION OF XPYTHON IS RELEASED
        # (and the kernel.json file contains the prefix_bundler info)
        if language == "python":
            prefix_bundler_name = "empack"

        

        prefix_bundler = get_prefix_bundler(name=prefix_bundler_name)
        prefix_bundler = prefix_bundler(addon=self, kernel_name=kernel_dir.name, static_dir=static_dir, **prefix_bundler_kwargs)
        
        for item in prefix_bundler.build(kernel_dir=static_dir / "kernels"/ kernel_dir.name):
            if item:
                yield item