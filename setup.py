from setuptools import setup

setup(
    name='jiradmin',
    version='0.1',
    py_modules=['jiradmin'],
    install_requires=[
        'click',
        'requests',
        'tabulate',
    ],
    entry_points='''
        [console_scripts]
        jiradmin=jiradmin:cli
    ''',
)