supervisor Cookbook
===================
Installs (Python) supervisor and provides resources to configure services


Requirements
------------
### Platforms
Supports Debian and RHEL based systems. Tested on Ubuntu 12.04, 10.04, CentOS 6.5.

### Cookbooks
- python


Attributes
----------
- `node['supervisor']['inet_port']` - The port on which you want to serve the internal web-based admin dashboard, e.g. `'localhost:9001'`
- `node['supervisor']['inet_username']` - The username for authentication to this HTTP server
- `node['supervisor']['inet_password']` - The password for authentication to this HTTP server (supports both cleartext and SHA-1 hashed passwords prefixed by `{SHA}`)
- `node['supervisor']['dir']` - location of supervisor config files
- `node['supervisor']['log_dir']` - location of supervisor logs
- `node['supervisor']['logfile_maxbytes']` - max bytes for the supervisord logfile before it is rotated rotated, default `'50MB'`
- `node['supervisor']['logfile_backups']` - the number of backups of that logfile to keep, default `10`
- `node['supervisor']['loglevel']` - the minimum severity for those log messages, default `'info'`
- `node['supervisor']['minfds']` - The minimum number of file descriptors that must be available before supervisord will start successfully.
- `node['supervisor']['minprocs']` - The minimum number of process descriptors that must be available before supervisord will start successfully.
- `node['supervisor']['version']` - Sets the version of supervisor to install, must be 3.0+ to use minprocs and minfds.
- `node['supervisor']['socket_file']` - location of supervisor socket file.


Resources/Providers
-------------------
### supervisor\_service

#### Actions

The default action is the array `[:enable, :start]`. Actions use the `supervisorctl` program.

- :enable - enables the service at boot time
- :disable - disables the service at boot time
- :start - starts the service
- :stop - stops the service
- :restart - restarts the service
- :reload - reloads the service

#### Attribute Parameters

- `:service_name` - (*Name Attribute*), a string, name of the service

The following attributes are used in the program.conf.erb as the values for the corresponding configuration option. See [the supervisor documentation](http://supervisord.org/configuration.html#program-x-section-values) for more information about each setting, including applicable defaults.

- `:command` - string
- `:process_name` - string
- `:numprocs` - integer
- `:numprocs_start` - integer
- `:priority` - integer
- `:autostart` - true or false
- `:autorestart` - string, symbol, true or false
- `:startsecs` - integer
- `:startretries` - integer
- `:exitcodes` - array
- `:stopsignal` - string or symbol
- `:stopwaitsecs` - integer
- `:user` - string or nil
- `:redirect_stderr` - true or false
- `:stdout_logfile` - string
- `:stdout_logfile_maxbytes` - string
- `:stdout_logfile_backups` - string
- `:stdout_capture_maxbytes` - string
- `:stdout_events_enabled` - true or false
- `:stderr_logfile` - string
- `:stderr_logfile_maxbytes` - string
- `:stderr_logfile_backups` - integer
- `:stderr_capture_maxbytes` - string
- `:stderr_events_enabled` - true or false
- `:environment`- hash
- `:directory`- string or nil
- `:umask` - string or nil
- `:serverurl` - string

#### Examples

```ruby
supervisor_service "celery" do
  action :enable
  autostart false
  user "nobody"
end
```


Recipes
-------
### default
Includes the python recipe, installs the supervisor PIP package and sets up supervisor.


License & Authors
-----------------
- Author:: Noah Kantrowitz <noah@opscode.com>
- Author:: Gilles Devaux <gilles.devaux@gmail.com>
- Author:: Sam Clements <sam.clements@datasift.com>
- Author:: Chris Jerdonek <chris.jerdonek@gmail.com>

```text
Copyright:: 2011-2012, Opscode, Inc <legal@opscode.com>
Copyright:: 2011, Formspring.me

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
