#!/usr/bin/env rake

# Style tests. Rubocop and Foodcritic
namespace :style do
  begin
    require 'rubocop/rake_task'
    desc 'Run Ruby style checks'
    RuboCop::RakeTask.new(:ruby)
  rescue LoadError
    puts '>>>>> Rubocop gem not loaded, omitting tasks' unless ENV['CI']
  end

  begin
    require 'foodcritic'

    desc 'Run Chef style checks'
    FoodCritic::Rake::LintTask.new(:chef) do |t|
      t.options = {
        fail_tags: ['any']
      }
    end
  rescue LoadError
    puts '>>>>> foodcritic gem not loaded, omitting tasks' unless ENV['CI']
  end
end

desc 'Run all style checks'
task style: ['style:chef', 'style:ruby']

namespace :unit do
  begin
    require 'rspec/core/rake_task'
    desc 'Runs specs with chefspec.'
    RSpec::Core::RakeTask.new(:rspec)
  rescue LoadError
    puts '>>>>> chefspec gem not loaded, omitting tasks' unless ENV['CI']
  end
end

desc 'Run all unit tests'
task unit: ['unit:rspec']

# Integration tests. Kitchen.ci
namespace :integration do
  begin
    require 'kitchen/rake_tasks'

    desc 'Run kitchen integration tests'
    Kitchen::RakeTasks.new
  rescue LoadError
    puts '>>>>> Kitchen gem not loaded, omitting tasks' unless ENV['CI']
  end
end

desc 'Run all tests on Travis'
task travis: ['unit']

# Default
# task default: ['unit', 'style', 'integration:kitchen:all']
task default: ['unit', 'style', 'integration:kitchen:all']
