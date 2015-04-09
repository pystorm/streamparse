# resources/config.rb

actions(:render, :delete)
default_action(:render)

attribute(:path,   kind_of: String, name_attribute: true)
attribute(:user,   kind_of: String, default: 'zookeeper')
attribute(:config, kind_of: Hash,   required: true)
