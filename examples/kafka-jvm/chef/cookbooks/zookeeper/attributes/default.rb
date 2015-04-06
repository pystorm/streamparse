# attributes/default.rb

default[:zookeeper][:version]     = '3.4.6'
default[:zookeeper][:checksum]    = '01b3938547cd620dc4c93efe07c0360411f4a66962a70500b163b59014046994'
default[:zookeeper][:mirror]      = 'http://www.poolsaboveground.com/apache/zookeeper'
default[:zookeeper][:user]        = 'zookeeper'
default[:zookeeper][:install_dir] = '/opt/zookeeper'
default[:zookeeper][:use_java_cookbook] = true

# One of: 'upstart', 'runit', 'exhibitor'
default[:zookeeper][:service_style] = 'runit'

default[:zookeeper][:config] = {
  clientPort: 2181,
  dataDir: '/var/lib/zookeeper',
  tickTime: 2000
}
