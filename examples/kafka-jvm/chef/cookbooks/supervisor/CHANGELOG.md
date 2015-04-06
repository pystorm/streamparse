supervisor Cookbook CHANGELOG
=============================
This file is used to list changes made in each version of the supervisor cookbook.


v0.4.10
-------
### Bug
- **[COOK-3784](https://tickets.opscode.com/browse/COOK-3784)** - Only remove newlines when absolutely necessary


v0.4.8
------
### Bug
- **[COOK-3448](https://tickets.opscode.com/browse/COOK-3448)** - Remove duplicate `:restart` provider

v0.4.6
------
### Bug
- **[COOK-3312](https://tickets.opscode.com/browse/COOK-3312)** - Sort environment variables
- **[COOK-3098](https://tickets.opscode.com/browse/COOK-3098)** - Fix supervisor notifications
- **[COOK-3037](https://tickets.opscode.com/browse/COOK-3037)** - Add missing priority option in template

v0.4.4
------
### Bug:
- [COOK-3284]: supervisor cookbook upgrades distribute to 0.7.3, breaks pip

v0.4.2
------
### Bug
- [COOK-2601]: support supervisor on SmartOS
- [COOK-2980]: supervisor cookbook has foodcritic errors

v0.4.0
------
- [COOK-2157] - add `inet_http_server` and logfile config settings

v0.3.0
------
- [COOK-2053] - Supervisor cookbook missing stopasgroup

v0.2.0
------
- [COOK-1720] - support for 'minfds' or 'minprocs' parameters
