#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
from os.path import abspath
from os.path import dirname
from os.path import exists
from os.path import join


if __name__ == "__main__":
    base_path = dirname(dirname(abspath(__file__)))
    print("Project path: {0}".format(base_path))
    env_path = join(base_path, ".tox", "bootstrap")
    if sys.platform == "win32":
        bin_path = join(env_path, "Scripts")
    else:
        bin_path = join(env_path, "bin")
    if not exists(env_path):
        import subprocess

        print("Making bootstrap env in: {0} ...".format(env_path))
        try:
            subprocess.check_call(["virtualenv", env_path])
        except subprocess.CalledProcessError:
            subprocess.check_call([sys.executable, "-m", "virtualenv", env_path])
        print("Installing `jinja2` into bootstrap environment...")
        subprocess.check_call([join(bin_path, "pip"), "install", "jinja2"])
    python_executable = join(bin_path, "python")
    if not os.path.samefile(python_executable, sys.executable):
        print("Re-executing with: {0}".format(python_executable))
        os.execv(python_executable, [python_executable, __file__])

    import jinja2

    import subprocess

    jinja = jinja2.Environment(
        loader=jinja2.FileSystemLoader(join(base_path, "ci", "templates")),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True
    )

    tox_environments = [
        line.strip()
        # WARNING: 'tox' must be installed globally or in the project's virtualenv
        for line in subprocess.check_output(['tox', '--listenvs'], universal_newlines=True).splitlines()
    ]
    tox_environments = [line for line in tox_environments if line not in ['clean', 'report', 'docs', 'check']]

    for name in os.listdir(join("ci", "templates")):
        with open(join(base_path, name), "w") as fh:
            fh.write(jinja.get_template(name).render(tox_environments=tox_environments))
        print("Wrote {}".format(name))
    print("DONE.")
