default[:storm][:deploy][:user] = ::File.exists?("/home/vagrant") ? "vagrant" : "ubuntu"
default[:storm][:deploy][:group] = ::File.exists?("/home/vagrant") ? "vagrant" : "ubuntu"

default[:storm][:nimbus][:host] = "192.168.42.10"
default[:storm][:supervisor][:hosts] = [ "192.168.42.20" ]

default[:storm][:nimbus][:childopts] = "-Xmx512m -Djava.net.preferIPv4Stack=true"

default[:storm][:supervisor][:childopts] = "-Xmx512m -Djava.net.preferIPv4Stack=true"
default[:storm][:supervisor][:workerports] = (6700..6706).to_a
default[:storm][:worker][:childopts] = "-Xmx512m -Djava.net.preferIPv4Stack=true"

default[:storm][:ui][:childopts] = "-Xmx512m -Djava.net.preferIPv4Stack=true"

default[:storm][:version] = "0.9.4"

