Vagrant.configure("2") do |config|
  config.vm.box = "streamparse-box"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"
  # Private networking using instead of port-forwarding which has a number of
  # issues. Effectively all services will be available from this IP.
  config.vm.network "private_network", ip: "192.168.50.50"
  config.vm.hostname = "streamparse-box"
  config.ssh.forward_agent = true

  # Assumes you're using Virtualbox
  config.vm.provider "virtualbox" do |v|
    # Give our box a friendly name inside Virtualbox
    v.name = "streamparse-kafka-storm-box"
    # allow software-defined networking
    v.customize ['modifyvm', :id, '--nicpromisc1', 'allow-all']
    # limit CPU usage
    v.customize ["modifyvm", :id, "--cpuexecutioncap", "70"]
    # 1.6gb of RAM
    v.memory = 1536
    # 2 vCPUs
    v.cpus = 2
  end

  config.vm.provision "chef_solo" do |chef|
    chef.cookbooks_path = ["chef/cookbooks"]
    chef.add_recipe "apt"
    chef.add_recipe "java::default"
    chef.add_recipe "python"
    chef.add_recipe "supervisor"
    chef.add_recipe "storm::singlenode"
    chef.add_recipe "streamparse"
    chef.add_recipe "apache_kafka"

    chef.json = {
      :java => {
        :oracle => {
          "accept_oracle_download_terms" => true
        },
        :install_flavor => "openjdk",
        :jdk_version => "7"
      },

      :python => {
        "min_version" => "2.7.5",
      },

      :zookeeper => {
        :client_port => "2181"
      },

      :storm => {
        :deploy => {
          :user => "storm",
          :group => "storm"
        },
        :nimbus => {
          :host => "streamparse-box",
          :childopts => "-Xmx128m"
        },
        :supervisor => {
          :hosts => ["streamparse-box"],
          :childopts => "-Xmx128m"
        },
        :worker => {
          :childopts => "-Xmx128m"
        },
        :ui => {
          :host => "streamparse-box",
          :childopts => "-Xmx128m"
        }
      },

      :apache_kafka => {
        :conf => {
           :server => {
              :entries => {
                "advertised.host.name" => "streamparse-box"
              }
           }
        }
      }
    }
  end
end
