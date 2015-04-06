#
# Cookbook:: runit
# Libraries:: helpers
#
# Author: Joshua Timberman <joshua@getchef.com>
# Copyright (c) 2014, Chef Software, Inc. <legal@getchef.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

require 'chef/mixin/shell_out'
include Chef::Mixin::ShellOut
module Runit
  module Helpers
    def runit_installed?
      return true if runit_rpm_installed? || (runit_executable? && runit_sv_works?)
    end

    def runit_executable?
      ::File.executable?(node['runit']['executable'])
    end

    def runit_sv_works?
      sv = shell_out("#{node['runit']['sv_bin']} --help")
      sv.exitstatus == 100 && sv.stderr =~ /usage: sv .* command service/
    end

    def runit_rpm_installed?
      shell_out('rpm -qa | grep -q "^runit"').exitstatus == 0
    end
  end
end

Chef::Recipe.send(:include, Runit::Helpers)
Chef::Resource.send(:include, Runit::Helpers)
