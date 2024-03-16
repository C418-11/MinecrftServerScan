# -*- coding: utf-8 -*-


__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1Dev"

import os
import re
import subprocess
from typing import Union

from Cython.Build import cythonize
from setuptools import setup


def _get_dependency_versions() -> dict[str, str]:
    result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True)

    dependencies = result.stdout.split('\n')
    dependency_versions = {}
    for dep in dependencies:
        if not dep:
            continue
        dep_name, dep_version = dep.split('==')
        dependency_versions[dep_name] = dep_version

    return dependency_versions


def _get_all_extension_files(directory, extension=".py") -> list:
    _py_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                _py_files.append(os.path.join(root, file))
    return _py_files


def _make_path(path_a, path_b):
    return os.path.normpath(os.path.join(path_a, path_b))


class PyToPyd:
    def __init__(self, output_dir: Union[str, None] = None):
        if output_dir is None:
            output_dir = os.path.dirname(__file__)

        self.output_dir = _make_path(output_dir, "Build")
        self.c_path = _make_path(self.output_dir, "c")
        self.temp_path = _make_path(self.output_dir, "temp")
        self.pyd_path = _make_path(self.output_dir, "pyd")

    def _make_c_file(self, file):
        return cythonize(file, build_dir=self.c_path)

    @staticmethod
    def _dependency_versions():
        dependency_versions = []
        for dep, ver in _get_dependency_versions().items():
            dependency_versions.append(dep + "==" + ver)
        return dependency_versions

    def make(self, file, sub_path: str = ''):
        os.makedirs(_make_path(self.pyd_path, sub_path), exist_ok=True)
        setup(
            ext_modules=self._make_c_file(file),
            script_name="setup.py",
            script_args=[
                "build_ext",
                "--build-lib",
                _make_path(self.pyd_path, sub_path),
                "--build-temp",
                _make_path(self.temp_path, sub_path),
            ],
            install_requires=self._dependency_versions(),
            author="C418____11",
            author_email="553515788@qq.com",
            url="https://github.com/C418-11/ComputerStatusRecorder",
        )

    def make_all(self, dir_path, sub_path: str = ''):
        root_dir = os.path.dirname(dir_path)

        for path in _get_all_extension_files(dir_path):

            if os.path.relpath(path, root_dir).lower().startswith("lib"):
                to_path = sub_path
            else:
                to_path = sub_path + str(os.path.relpath(os.path.dirname(path), root_dir))

            self.make(path, sub_path=to_path)


def _rename_file(file_name, replace, to):
    print(f"Renaming {file_name}")
    new_file_name = re.sub(replace, to, file_name)
    if file_name != new_file_name:
        os.rename(file_name, new_file_name)
    print(f"Renamed {file_name} to {new_file_name}")


def _rename_all(dir_path, replace, to, extension=".pyd"):
    for path in _get_all_extension_files(dir_path, extension):
        _rename_file(path, replace, to)


def _main():
    type_ = input("1: Pyd Default Features, 2: Pyd Other Features, 3: Print Depends, 4: Exit\n")

    compiler = PyToPyd()

    def a():
        compiler.make_all(r"D:\source_code\python\ComputerStatusRecorder\DefaultFeatures")
        compiler.make_all(r"D:\source_code\python\ComputerStatusRecorder\Recorder")
        compiler.make_all(r"D:\source_code\python\ComputerStatusRecorder\Monitor")
        compiler.make_all(r"D:\source_code\python\ComputerStatusRecorder\Lib")
        _rename_all(compiler.pyd_path, r".cp312-win_amd64", r"")

    def b():
        compiler.make_all(r"D:\source_code\python\ComputerStatusRecorder\Features")
        _rename_all(compiler.pyd_path, r".cp312-win_amd64", r"")

    if '1' in type_:
        a()
    if '2' in type_:
        b()
    if '3' in type_:
        for dep, ver in _get_dependency_versions().items():
            print(f"{dep}=={ver}")
    if '4' in type_:
        exit()


if __name__ == "__main__":
    _main()

__all__ = ("PyToPyd",)
