from invoke import run, task
import os


@task
def build_docs():
    run("sphinx-build doc/source doc/_build")


@task
def test(docs=False):
    run("nosetests --processes=-1")


@task
def lint():
    for src in os.listdir("streamparse"):
        if src.endswith(".py"):
            run("pyflakes streamparse/{}".format(src))


@task(pre=[test])
def build(docs=False):
    run("python setup.py build")
    if docs:
        build_docs()


@task
def develop():
    run("python setup.py develop")


@task
def upload():
    run('git checkout-index -a --prefix {}/'.format('_release'))
    run("cd _release && python setup.py sdist upload")
    run("rm -Rf _release")
