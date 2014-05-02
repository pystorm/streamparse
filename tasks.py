from invoke import run, task
import os

@task
def lint():
    for src in os.listdir("streamparse"):
        if src.endswith(".py"):
            run("pyflakes streamparse/{}".format(src))

@task
def build(docs=False):
    run("python setup.py build")
    if docs:
        run("sphinx-build doc/source doc/_build")

@task
def develop():
    run("python setup.py develop")
