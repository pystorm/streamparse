name              'runit'
maintainer        'Heavy Water Operations, LLC.'
maintainer_email  'support@hw-ops.com'
license           'Apache 2.0'
description       'Installs runit and provides runit_service definition'
long_description  IO.read(File.join(File.dirname(__FILE__), 'README.md'))
version           '1.5.18'

recipe 'runit', 'Installs and configures runit'

%w{ ubuntu debian gentoo centos redhat amazon scientific oracle enterpriseenterprise }.each do |os|
  supports os
end

depends 'build-essential'
depends 'yum', '~> 3.0'
depends 'yum-epel'
