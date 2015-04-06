# libraries/default.rb

module Zk
  module Config

    # Zookeeper uses a Java properties file style of configuration. This helper
    # method will render a hash in that style.
    def render_zk_config(config, lead=nil)
      rendered = ""

      config.each_pair do |k,v|
        if lead
          rendered << "#{lead}."
        end

        if v.is_a?(Hash)
          rendered << render_zk_config(v, k)
        else
          rendered << "#{k}=#{v}\n"
        end
      end

      return rendered
    end

  end
end
