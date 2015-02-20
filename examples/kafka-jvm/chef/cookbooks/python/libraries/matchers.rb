if defined?(ChefSpec)
  def install_python_pip(package_name)
    ChefSpec::Matchers::ResourceMatcher.new(:python_pip, :install, package_name)
  end

  def upgrade_python_pip(package_name)
    ChefSpec::Matchers::ResourceMatcher.new(:python_pip, :upgrade, package_name)
  end

  def remove_python_pip(package_name)
    ChefSpec::Matchers::ResourceMatcher.new(:python_pip, :remove, package_name)
  end

  def purge_python_pip(package_name)
    ChefSpec::Matchers::ResourceMatcher.new(:python_pip, :purge, package_name)
  end

  def create_python_virtualenv(virtualenv_name)
    ChefSpec::Matchers::ResourceMatcher.new(:python_virtualenv, :create, virtualenv_name)
  end

  def delete_python_virtualenv(virtualenv_name)
    ChefSpec::Matchers::ResourceMatcher.new(:python_virtualenv, :delete, virtualenv_name)
  end
end
