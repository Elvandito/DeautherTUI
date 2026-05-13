import os
import stat
import subprocess
from setuptools import setup
from setuptools.command.install import install

SCRIPT_CONTENT = """\
#!/usr/bin/python3
import sys
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
from deauther import main
main()
"""

INSTALL_PATHS = ["/usr/local/bin/deauther", "/usr/bin/deauther"]


class PostInstallCommand(install):
    """Fix shebangs after install to use the global system Python."""

    def run(self):
        super().run()
        for path in INSTALL_PATHS:
            if os.path.exists(path):
                try:
                    with open(path, "w") as f:
                        f.write(SCRIPT_CONTENT)
                    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                    print(f"Fixed shebang in {path}")
                except Exception as e:
                    print(f"Warning: could not fix {path}: {e}")


setup(
    name='deauther',
    version='1.0.0',
    py_modules=['deauther'],
    entry_points={
        'console_scripts': [
            'deauther=deauther:main',
        ],
    },
    install_requires=[
        'textual',
        'rich',
        'pandas',
    ],
    author='Elvan',
    description='WiFi Deauther TUI',
    cmdclass={
        'install': PostInstallCommand,
    },
)
