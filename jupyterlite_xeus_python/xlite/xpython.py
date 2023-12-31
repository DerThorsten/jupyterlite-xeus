from pathlib import Path
from empack.pack import DEFAULT_CONFIG_PATH, pack_env
from empack.file_patterns import pkg_file_filter_from_yaml

from .xlite import XLiteBuilderBase

class XLiteBuilderBase:
    def __init__(self, addon,kernel_name, static_dir):
        self.addon = addon
        self.kernel_name = kernel_name
        self.static_dir = static_dir
        self.packages_dir = Path(self.static_dir) / "kernel_packages"

    
    def build(self, kernel_dir):
        yield 


class XPythonBuilder(XLiteBuilderBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def build(self, kernel_dir):

        prefix_path = Path(self.addon.prefix)

        # temp dir for the packed env
        out_path = Path(self.addon.cwd.name) / "packed_env"
        out_path.mkdir(parents=True, exist_ok=True)

        # Pack the environment
        file_filters = pkg_file_filter_from_yaml(DEFAULT_CONFIG_PATH)

        pack_env(
            env_prefix=prefix_path,
            relocate_prefix="/",
            outdir=out_path,
            use_cache=True,
            file_filters=file_filters
        )

        # copy all the packages to the packages dir 
        # (this is shared between multiple xeus-python kernels)
        for pkg_path in out_path.iterdir():
            if pkg_path.name.endswith(".tar.gz"):
                yield dict(
                    name=f"xeus:{self.kernel_name}:copy_package:{pkg_path.name}",
                    actions=[(self.addon.copy_one, [pkg_path, self.packages_dir / pkg_path.name ])],
                )

        # copy the empack_env_meta.json
        # this is individual for xeus-python kernel
        empack_env_meta = "empack_env_meta.json"
        yield dict(
            name=f"xeus:{self.kernel_name}:copy_env_file:{empack_env_meta}",
            actions=[(self.addon.copy_one, [out_path / empack_env_meta, Path(kernel_dir)/ empack_env_meta ])],
        )