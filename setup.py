from setuptools import setup

setup(
    name='chess_AI',
    version='0.1',
    description='Machine Learning AI chess engine',
    author='Bas Dirkse',
    author_email='basdirkse90@gmail.com',
    license='All rights reserved',
    packages=[
        'chess_AI',
    ],
    package_dir={'chess_AI': 'chess_AI'},
    install_requires=[
        'numpy',
    ]
)
