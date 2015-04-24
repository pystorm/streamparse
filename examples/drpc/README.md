# Install streamparse

In the streamparse directory, run

    sudo python setup.py develop

In order to have the `sparse` shell command available system-wide.


# Install Leiningen

Follow [these instructions](http://leiningen.org/) to install Leiningen > 2.0.
On OSX you can also use homebrew to install leiningen

    brew install leiningen


# Compile and run the topology locally

    lein deps
    lein compile
    lein run -m streamparse.AdderTopology
