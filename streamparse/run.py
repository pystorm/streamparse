import importlib

from docopt import docopt

def main():
    """streamparse.run: run a bolt/spout class

    This is internal to streamparse and is used to run spout and bolt
    classes via ``python -m streamparse.run <class name>``.

    Usage:
        run <target_class>

    Options:
        -h --help   Show this screen
    """
    # Import the component class and run it
    args = docopt(main.__doc__)
    mod_name, cls_name = args['<target_class>'].rsplit('.', 1)
    mod = importlib.import_module(mod_name)
    cls = getattr(mod, cls_name)
    cls().run()

if __name__ == '__main__':
    main()
