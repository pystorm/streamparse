**Table of Contents**

- [Zookeeper](#zookeeper)
  - [Usage](#usage)
    - [Resources](#resources)
      - [zookeeper](#zookeeper)
      - [zookeeper_config](#zookeeper_config)
  - [Errata](#errata)
  - [Author and License](#author-and-license)

# Zookeeper
[Zookeeper](http://zookeeper.apache.org/) is a coordination and discovery
service maintained by the Apache Software Foundation.

This cookbook focuses on deploying Zookeeper via Chef.

## Usage
This cookbook is primarily a library cookbook. It implements a `zookeeper`
resource to handle the installation and configuration of Zookeeper. It ships
with a default recipe for backwards compatibility pre-LWRP which will work
fine, but is really just an example.

Use the "install" recipe to install the binaries, but perform no further actions.

### Resources
This cookbook ships with one resource, with future plans for two more covering
service management and configuration rendering.

#### zookeeper
The `zookeeper` resource is responsible for installing and (eventually)
uninstalling Zookeeper from a node.

Actions: `:install`, `:uninstall`

Parameters:
* `version`: Version of Zookeeper to install (name attribute)
* `user`: The user who will eventually run Zookeeper (default: `'zookeeper'`)
* `mirror`: The mirror to obtain Zookeeper from (required)
* `checksum`: Checksum for the Zookeeper download file
* `install_dir`: Which directory to install Zookeeper to (default:
  `'/opt/zookeeper')

Example:
``` ruby
zookeeper '3.4.6' do
  user     'zookeeper'
  mirror   'http://www.poolsaboveground.com/apache/zookeeper'
  checksum '01b3938547cd620dc4c93efe07c0360411f4a66962a70500b163b59014046994'
  action   :install
end
```

#### zookeeper_config
This resource renders a Zookeeper configuration file. Period-delimited
parameters can be specified either as a flat hash, or by embeddeding each
sub-section within a separate hash. See the example below for an example.

Actions: `:render`, `:delete`

Parameters:
* `user`: The user to give ownership of the file to (default: `zookeeper`)
* `config`: Hash of configuration parameters to add to the file
* `path`: Path to write the configuration file to.

Example:
``` ruby
config_hash = {
  clientPort: 2181, 
  dataDir: '/mnt/zk', 
  tickTime: 2000,
  autopurge: {
    snapRetainCount: 1,
    purgeInterval: 1
  }
}

zookeeper_config '/opt/zookeeper/zookeeper-3.4.6/conf/zoo.cfg' do
  config config_hash
  user   'zookeeper'
  action :render
end
```

## Errata
* Version 1.4.7 on the community site is in fact version 1.4.8.

## Author and License
Simple Finance <ops@simple.com>
Apache License, Version 2.0

