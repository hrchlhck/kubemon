from setuptools import setup

setup(
    name='kubemon',
    version='2.0.0',
    descripton='A tool for distributed container monitoring over Kubernetes',
    url='https://github.com/hrchlhck/kubemon',
    author='Pedro (vpemfh7) Horchulhack',
    author_email='pedro.horchulhack@ppgia.pucpr.br',
    license='MIT',
    packages=[
        'kubemon', 'kubemon.collector',
        'kubemon.cli', 'kubemon.monitors',
        'kubemon.exceptions', 'kubemon.entities'
    ],
    install_requires=['wheel', 'pandas', 'requests', 'psutil', 'docker', 'flask']
)