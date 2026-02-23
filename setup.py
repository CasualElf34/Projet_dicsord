"""
Setup pour packager Likoo comme application desktop
"""

from setuptools import setup, find_packages

setup(
    name='Likoo',
    version='1.0.0',
    description='Application Discord-like avec interface flottante',
    author='Your Name',
    python_requires='>=3.8',
    install_requires=[
        'Flask==2.3.2',
        'Flask-CORS==4.0.0',
    ],
    entry_points={
        'console_scripts': [
            'likoo-server=server:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['*.html', '*.css', '*.js'],
    },
)
