from setuptools import setup, find_packages

def read_version(fname="expcol/version.py"):
    exec(compile(open(fname, encoding="utf-8").read(), fname, "exec"))
    return locals()["__version__"]

setup(
    name='expcol',
    version=read_version(),
    description='Create collision detection using expression node.',
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    readme="README.md",
    author='Hiroyuki Akasaki',
    license="MIT",
    packages=find_packages(),
    url="https://github.com/akasaki1211/maya_expressionCollision"
)