from invoke import run, task
import os

@task
def lint():
    for src in os.listdir("pystorm"):
        if src.endswith(".py"):
            run("pyflakes pystorm/{}".format(src))
            #run("pep8 pystorm/{}".format(src))

@task
def build(docs=False):
    run("python setup.py build")
    if docs:
        run("sphinx-build doc/source doc/_build")

@task
def develop():
    run("python setup.py develop")
