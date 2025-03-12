# -*- coding: utf-8 -*-
import importlib
import sys
from importlib import metadata
from types import ModuleType
from typing import Callable

from sinapsis_core.utils.env_var_keys import SinapsisEnvVarDefaults
from sinapsis_core.utils.logging_utils import sinapsis_logger

_root_lib_path = "sinapsis.templates"
_core_lib_path = "sinapsis_core.template_base"
_template_lookup = {
    "CopyDataContainer": f"{_core_lib_path}.copy_data_container",
    "DisplayHelloWorld": f"{_root_lib_path}.display_hello_world",
    "HelloWorld": f"{_root_lib_path}.hello_world",
    "InputTemplate": f"{_core_lib_path}.input_template",
    "MergeDataFlow": f"{_core_lib_path}.merge_data_flow",
    "OutputTemplate": f"{_core_lib_path}.output_template",
    "SplitDataFlow": f"{_core_lib_path}.split_data_flow",
    "TransferDataContainer": f"{_core_lib_path}.transfer_data_container",
}


def _import_template_package(package_name: str) -> dict:
    available_templates = {}
    try:
        template_module = importlib.import_module(package_name)
        template_names = getattr(template_module, "__all__")
        for name in template_names:
            available_templates[name] = package_name
    except (ModuleNotFoundError, ImportError, AttributeError) as err:
        sinapsis_logger.debug(f"Skipping package: {package_name}, does it have a `templates` directory?\n\terr: {err}")
    return available_templates


def _read_from_additional_paths(template_name: str):
    def lazy_import(module_name, file_path):
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        loader = importlib.util.LazyLoader(spec.loader)
        spec.loader = loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        loader.exec_module(module)
        return module

    additional_paths = SinapsisEnvVarDefaults.ADDITIONAL_TEMPLATE_PATHS.value
    if not additional_paths or not isinstance(additional_paths, list):
        return None

    template_module_name = "templates"
    for idx, add_path in enumerate(additional_paths):
        m_name = f"{template_module_name}_{idx}"
        add_path_init = f"{add_path}__init__.py"
        t_module = lazy_import(m_name, add_path_init)

        if hasattr(t_module, template_name):
            return_template = getattr(t_module, template_name)
            return return_template

    return None


def smart_search() -> dict:
    excluded_dists = ["sinapsis_core"]
    available_sinapsis_templates: dict = {}

    for available_dist in metadata.distributions():
        dist_name = available_dist._normalized_name  # type:ignore[attr-defined]
        if dist_name.startswith("sinapsis_") and dist_name not in excluded_dists:
            sinapsis_logger.debug(f"Adding package {available_dist.name}=={available_dist.version}")
            available_sinapsis_templates |= _import_template_package(f"{dist_name}.templates")

    return available_sinapsis_templates


_template_lookup |= smart_search()


def __getattr__(name: str) -> Callable | ModuleType:
    if name in _template_lookup:
        module = importlib.import_module(_template_lookup[name])
        return getattr(module, name)
    else:
        try:
            module = _read_from_additional_paths(name)
            if module is not None:
                return module
        except FileNotFoundError as err:
            sinapsis_logger.error(err)

    raise AttributeError(
        f"Template `{name}` not found. Please ensure it is in {_root_lib_path}.\nIf you have"
        f"implemented a sinapsis package, please ensure it is installed,\n\t e.g., using uv|pdm|poetry|pip. "
        f"\notherwise, please set the `ADDITIONAL_TEMPLATE_PATHS` environment variable to make your"
        f"templates discoverable, e.g. \n\texport ADDITIONAL_TEMPLATE_PATHS='[\"path/to/my_package/templates/\"]'"
    )


__all__ = list(_template_lookup.keys())
