# providers/config.rb

include Zk::Config

use_inline_resources

def initialize(new_resource, run_context)
  super
  @path   = new_resource.path
  @config = new_resource.config
  @user   = new_resource.user
  @zoocfg = zookeeper_config_resource(@path)
end

action :render do
  @zoocfg.owner(@user)
  @zoocfg.group(@user)
  @zoocfg.content(render_zk_config(@config))
  @zoocfg.run_action(:create)
  new_resource.updated_by_last_action(@zoocfg.updated_by_last_action?)
end

action :delete do
  Chef::Log.info("Deleting Zookeeper config at #{@path}")
  FileUtils.rm(@path)
end

private

def zookeeper_config_resource(path='')
  return Chef::Resource::File.new(path, @run_context)
end
