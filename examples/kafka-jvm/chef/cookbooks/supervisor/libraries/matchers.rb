if defined?(ChefSpec)
  def enable_supervisor_service(service_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_service, :enable, service_name)
  end

  def disable_supervisor_service(service_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_service, :disable, service_name)
  end

  def start_supervisor_service(service_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_service, :start, service_name)
  end

  def stop_supervisor_service(service_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_service, :stop, service_name)
  end

  def restart_supervisor_service(service_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_service, :restart, service_name)
  end

  def enable_supervisor_group(group_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_group, :enable, group_name)
  end

  def disable_supervisor_group(group_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_group, :disable, group_name)
  end

  def start_supervisor_group(group_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_group, :start, group_name)
  end

  def stop_supervisor_group(group_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_group, :stop, group_name)
  end

  def restart_supervisor_group(group_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_group, :restart, group_name)
  end

  def reload_supervisor_group(group_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_group, :reload, group_name)
  end

  def enable_supervisor_fcgi(fcgi_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_fcgi, :enable, fcgi_name)
  end

  def disable_supervisor_fcgi(fcgi_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_fcgi, :disable, fcgi_name)
  end

  def start_supervisor_fcgi(fcgi_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_fcgi, :start, fcgi_name)
  end

  def stop_supervisor_fcgi(fcgi_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_fcgi, :stop, fcgi_name)
  end

  def restart_supervisor_fcgi(fcgi_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_fcgi, :restart, fcgi_name)
  end

  def reload_supervisor_fcgi(fcgi_name)
    ChefSpec::Matchers::ResourceMatcher.new(:supervisor_fcgi, :reload, fcgi_name)
  end
end
