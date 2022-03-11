from setuptools import setup, find_packages

VERSION = '2.2.3'
SHORT_DESCRIPTION = 'A tool for distributed container monitoring over Kubernetes'
REQUIRES = [
    'requests', 'psutil', 
    'docker', 'flask',
    'flask_restful',
    'gunicorn',
]

def _load_readme() -> str:
    with open('README.md', 'r') as fp:
        return fp.read()

setup(
    name='kubemon',
    version=VERSION,
    descripton=SHORT_DESCRIPTION,
    long_description=_load_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/hrchlhck/kubemon',
    author='Pedro Horchulhack',
    author_email='pedro.horchulhack@ppgia.pucpr.br',
    license='MIT',
    packages=find_packages(),
    install_requires=REQUIRES
)
