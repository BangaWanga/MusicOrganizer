from setuptools import setup

setup(
    name='LiveOrganizer',
    version='0.0.1',
    install_requires=[
        'importlib-metadata; python_version<"3.13"',
        'blinker==1.8.2',
        'click==8.1.7',
        'colorama==0.4.6',
        'Flask==3.0.3',
        'Flask-Cors==4.0.1',
        'itsdangerous==2.2.0',
        'Jinja2==3.1.4',
        'MarkupSafe==2.1.5',
        'Werkzeug==3.0.6',
    ],
)
