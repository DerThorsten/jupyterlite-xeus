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

from .xlite import get_xlite_builder
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
        language = kernel_spec["language"].lower()
        builder = get_xlite_builder(language)
        builder = builder(addon=self, kernel_name=kernel_dir.name, static_dir=static_dir)
        
        yield dict(
            name=f"xeus:copy_kernel:{kernel_dir.name}",
            actions=[(self.copy_one, [kernel_dir, static_dir / "kernels"/ kernel_dir.name ])],
        )
        for item in builder.build(kernel_dir=static_dir / "kernels"/ kernel_dir.name):
            if item:
                yield item