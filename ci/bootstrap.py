#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
from os.path import exists
from os.path import join
from os.path import dirname
from os.path import abspath


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
        except Exception:
            subprocess.check_call([sys.executable, "-m", "virtualenv", env_path])
        print("Installing `jinja2` into bootstrap environment ...")
        subprocess.check_call([join(bin_path, "pip"), "install", "jinja2"])
    activate = join(bin_path, "activate_this.py")
    exec(compile(open(activate, "rb").read(), activate, "exec"), dict(__file__=activate))

    import jinja2

    import subprocess


    jinja = jinja2.Environment(
        loader=jinja2.FileSystemLoader(join(base_path, "ci", "templates")),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True
    )

    tox_environments = [line.strip() for line in subprocess.check_output(['tox', '--listenvs']).splitlines()]
    tox_environments = [line for line in tox_environments if line not in ['clean', 'report', 'docs', 'check']]

    template_vars = {'tox_environments': tox_environments}
    for py_ver in '26 27 33 34 35 py'.split():
        template_vars['py%s_environments' % py_ver] = [x for x in tox_environments if x.startswith('py' + py_ver)]

    for name in os.listdir(join("ci", "templates")):
        with open(join(base_path, name), "w") as fh:
            fh.write(jinja.get_template(name).render(**template_vars))
        print("Wrote {}".format(name))
    print("DONE.")
