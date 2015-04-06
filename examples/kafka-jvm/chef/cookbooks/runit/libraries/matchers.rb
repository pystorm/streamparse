if defined?(ChefSpec)

  def start_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :start, service)
  end

  def stop_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :stop, service)
  end

  def enable_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :enable, service)
  end

  def disable_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :disable, service)
  end

  def restart_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :restart, service)
  end

  def reload_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :reload, service)
  end

  def status_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :status, service)
  end

  def once_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :once, service)
  end

  def hup_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :hup, service)
  end

  def cont_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :cont, service)
  end

  def term_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :term, service)
  end

  def kill_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :kill, service)
  end

  def up_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :up, service)
  end

  def down_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :down, service)
  end

  def usr1_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :usr1, service)
  end

  def usr2_runit_service(service)
    ChefSpec::Matchers::ResourceMatcher.new(:runit_service, :usr2, service)
  end

end
