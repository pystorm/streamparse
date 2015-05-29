Vagrant::Config.run do |config|

  cookbook_name = File.basename(Dir.getwd)

  config.vm.define :nimbus do |nimbus_config|
    nimbus_config.vm.box = "precise64"
    nimbus_config.vm.host_name = "nimbus"
    nimbus_config.vm.network(:hostonly, "192.168.42.10", :adapter => 2)

    config.vm.provision :chef_solo do |chef|
      chef.cookbooks_path = "./.."
      chef.add_recipe("#{cookbook_name}::nimbus")
    end

  end

  config.vm.define :supervisor do |supervisor_config|
    supervisor_config.vm.box = "precise64"
    supervisor_config.vm.host_name = "supervisor"
    supervisor_config.vm.network(:hostonly, "192.168.42.20", :adapter => 2)
    
    config.vm.provision :chef_solo do |chef|
      chef.cookbooks_path = "./.."
      chef.add_recipe("#{cookbook_name}::supervisor")
    end

  end
end
