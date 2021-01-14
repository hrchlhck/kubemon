from setuptools import setup

setup(
    name='sys-monitor',
    version='1.0.0',
    descripton='A Python tool for monitoring SLA in container orchestration environments',
    url='https://github.com/hrchlhck/sys-monitor',
    author='Pedro (vpemfh7) Horchulhack',
    author_email='vpemfh7@protonmail.com',
    license='MIT',
    install_requires=['pandas', 'requests', 'psutil']
)