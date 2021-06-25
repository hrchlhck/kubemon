from setuptools import setup

setup(
    name='kubemon',
    version='2.0.0',
    descripton='A tool for distributed container monitoring over Kubernetes',
    url='https://github.com/hrchlhck/kubemon',
    author='Pedro (vpemfh7) Horchulhack',
    author_email='pedro.horchulhack@ppgia.pucpr.br',
    license='MIT',
    install_requires=['pandas', 'requests', 'psutil', 'docker', 'addict', 'sty']
)