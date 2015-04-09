name              "python"
maintainer        "Noah Kantrowitz"
maintainer_email  "noah@coderanger.net"
license           "Apache 2.0"
description       "Installs Python, pip and virtualenv. Includes LWRPs for managing Python packages with `pip` and `virtualenv` isolated Python environments."
version           "1.4.6"

depends           "build-essential"
depends           "yum-epel"

recipe "python", "Installs python, pip, and virtualenv"
recipe "python::package", "Installs python using packages."
recipe "python::source", "Installs python from source."
recipe "python::pip", "Installs pip from source."
recipe "python::virtualenv", "Installs virtualenv using the python_pip resource."

%w{ debian ubuntu centos redhat fedora freebsd smartos }.each do |os|
  supports os
end
