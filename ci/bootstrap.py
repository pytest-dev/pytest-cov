#!/usr/bin/env python
import os
import pathlib
import subprocess
import sys

base_path: pathlib.Path = pathlib.Path(__file__).resolve().parent.parent
templates_path = base_path / 'ci' / 'templates'


def check_call(args):
    print('+', *args)
    subprocess.check_call(args)


def exec_in_env():
    env_path = base_path / '.tox' / 'bootstrap'
    if sys.platform == 'win32':
        bin_path = env_path / 'Scripts'
    else:
        bin_path = env_path / 'bin'
    if not env_path.exists():
        import subprocess

        print(f'Making bootstrap env in: {env_path} ...')
        try:
            check_call([sys.executable, '-m', 'venv', env_path])
        except subprocess.CalledProcessError:
            try:
                check_call([sys.executable, '-m', 'virtualenv', env_path])
            except subprocess.CalledProcessError:
                check_call(['virtualenv', env_path])
        print('Installing `jinja2` into bootstrap environment...')
        check_call([bin_path / 'pip', 'install', 'jinja2', 'tox'])
    python_executable = bin_path / 'python'
    if not python_executable.exists():
        python_executable = python_executable.with_suffix('.exe')

    print(f'Re-executing with: {python_executable}')
    print('+ exec', python_executable, __file__, '--no-env')
    os.execv(python_executable, [python_executable, __file__, '--no-env'])


def main():
    import jinja2

    print(f'Project path: {base_path}')

    jinja = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_path)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    tox_environments = [
        line.strip()
        # 'tox' need not be installed globally, but must be importable
        # by the Python that is running this script.
        # This uses sys.executable the same way that the call in
        # cookiecutter-pylibrary/hooks/post_gen_project.py
        # invokes this bootstrap.py itself.
        for line in subprocess.check_output([sys.executable, '-m', 'tox', '--listenvs'], universal_newlines=True).splitlines()
    ]
    tox_environments = [line for line in tox_environments if line.startswith('py')]
    for template in templates_path.rglob('*'):
        if template.is_file():
            template_path = template.relative_to(templates_path).as_posix()
            destination = base_path / template_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(jinja.get_template(template_path).render(tox_environments=tox_environments))
            print(f'Wrote {template_path}')
    print('DONE.')


if __name__ == '__main__':
    args = sys.argv[1:]
    if args == ['--no-env']:
        main()
    elif not args:
        exec_in_env()
    else:
        print(f'Unexpected arguments: {args}', file=sys.stderr)
        sys.exit(1)
