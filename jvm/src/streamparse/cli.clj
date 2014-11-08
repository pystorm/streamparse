(ns
  streamparse.cli
  (:require [clojure.pprint :as pp]
            [clojure.string :as s])
  (:gen-class))

(defn- tokenize-args
  "Reduce arguments sequence into [opt-type opt ?optarg?] vectors and a vector
  of remaining arguments. Returns as [option-tokens remaining-args].

  Expands clumped short options like \"-abc\" into:
  [[:short-opt \"-a\"] [:short-opt \"-b\"] [:short-opt \"-c\"]]

  If \"-b\" were in the set of options that require arguments, \"-abc\" would
  then be interpreted as: [[:short-opt \"-a\"] [:short-opt \"-b\" \"c\"]]

  Long options with `=` are always parsed as option + optarg, even if nothing
  follows the `=` sign.

  If the :in-order flag is true, the first non-option, non-optarg argument
  stops options processing. This is useful for handling subcommand options."
  [required-set args & options]
  (let [{:keys [in-order]} (apply hash-map options)]
    (loop [opts [] argv [] [car & cdr] args]
      (if car
        (condp re-seq car
          ;; Double dash always ends options processing
          #"^--$" (recur opts (into argv cdr) [])
          ;; Long options with assignment always passes optarg, required or not
          #"^--\S+=" (recur (conj opts (into [:long-opt] (s/split car #"=" 2)))
                            argv cdr)
          ;; Long options, consumes cdr head if needed
          #"^--" (let [[optarg cdr] (if (contains? required-set car)
                                      [(first cdr) (rest cdr)]
                                      [nil cdr])]
                   (recur (conj opts (into [:long-opt car] (if optarg [optarg] [])))
                          argv cdr))
          ;; Short options, expands clumped opts until an optarg is required
          #"^-." (let [[os cdr] (loop [os [] [c & cs] (rest car)]
                                  (let [o (str \- c)]
                                    (if (contains? required-set o)
                                      (if (seq cs)
                                        ;; Get optarg from rest of car
                                        [(conj os [:short-opt o (s/join cs)]) cdr]
                                        ;; Get optarg from head of cdr
                                        [(conj os [:short-opt o (first cdr)]) (rest cdr)])
                                      (if (seq cs)
                                        (recur (conj os [:short-opt o]) cs)
                                        [(conj os [:short-opt o]) cdr]))))]
                   (recur (into opts os) argv cdr))
          (if in-order
            (recur opts (into argv (cons car cdr)) [])
            (recur opts (conj argv car) cdr)))
        [opts argv]))))

;;
;; Legacy API
;;

(defn- build-doc [{:keys [switches docs default]}]
  [(apply str (interpose ", " switches))
   (or (str default) "")
   (or docs "")])

(defn- banner-for [desc specs]
  (when desc
    (println desc)
    (println))
  (let [docs (into (map build-doc specs)
                   [["--------" "-------" "----"]
                    ["Switches" "Default" "Desc"]])
        max-cols (->> (for [d docs] (map count d))
                      (apply map (fn [& c] (apply vector c)))
                      (map #(apply max %)))
        vs (for [d docs]
             (mapcat (fn [& x] (apply vector x)) max-cols d))]
    (doseq [v vs]
      (pp/cl-format true "~{ ~vA  ~vA  ~vA ~}" v)
      (prn))))

(defn- name-for [k]
  (s/replace k #"^--no-|^--\[no-\]|^--|^-" ""))

(defn- flag-for [^String v]
  (not (.startsWith v "--no-")))

(defn- opt? [^String x]
  (.startsWith x "-"))

(defn- flag? [^String x]
  (.startsWith x "--[no-]"))

(defn- end-of-args? [x]
  (= "--" x))

(defn- spec-for
  [arg specs]
  (->> specs
       (filter (fn [s]
                   (let [switches (set (s :switches))]
                     (contains? switches arg))))
       first))

(defn- default-values-for
  [specs]
  (reduce (fn [m s]
            (if (contains? s :default)
              ((:assoc-fn s) m (:name s) (:default s))
              m))
          {} specs))

(defn- apply-specs
  [specs args]
  (loop [options    (default-values-for specs)
         extra-args []
         args       args]
    (if-not (seq args)
      [options extra-args]
      (let [opt  (first args)
            spec (spec-for opt specs)]
        (cond
         (end-of-args? opt)
         (recur options (into extra-args (vec (rest args))) nil)

         (and (opt? opt) (nil? spec))
         (throw (Exception. (str "'" opt "' is not a valid argument")))

         (and (opt? opt) (spec :flag))
         (recur ((spec :assoc-fn) options (spec :name) (flag-for opt))
                extra-args
                (rest args))

         (opt? opt)
         (recur ((spec :assoc-fn) options (spec :name) ((spec :parse-fn) (second args)))
                extra-args
                (drop 2 args))

         :default
         (recur options (conj extra-args (first args)) (rest args)))))))

(defn- switches-for
  [switches flag]
  (-> (for [^String s switches]
        (cond
         (and flag (flag? s))            [(s/replace s #"\[no-\]" "no-") (s/replace s #"\[no-\]" "")]
         (and flag (.startsWith s "--")) [(s/replace s #"--" "--no-") s]
         :default                        [s]))
      flatten))

(defn- generate-spec
  [raw-spec]
  (let [[switches raw-spec] (split-with #(and (string? %) (opt? %)) raw-spec)
        [docs raw-spec]     (split-with string? raw-spec)
        options             (apply hash-map raw-spec)
        aliases             (map name-for switches)
        flag                (or (flag? (last switches)) (options :flag))]
    (merge {:switches (switches-for switches flag)
            :docs     (first docs)
            :aliases  (set aliases)
            :name     (keyword (last aliases))
            :parse-fn identity
            :assoc-fn assoc
            :flag     flag}
           (when flag {:default false})
           options)))

(defn- normalize-args
  "Rewrite arguments sequence into a normalized form that is parsable by cli."
  [specs args]
  (let [required-opts (->> specs
                           (filter (complement :flag))
                           (mapcat :switches)
                           (into #{}))
        ;; Preserve double-dash since this is a pre-processing step
        largs (take-while (partial not= "--") args)
        rargs (drop (count largs) args)
        [opts largs] (tokenize-args required-opts largs)]
    (concat (mapcat rest opts) largs rargs)))

(defn cli
  "THIS IS A LEGACY FUNCTION and may be deprecated in the future. Please use
  clojure.tools.cli/parse-opts in new applications.

  Parse the provided args using the given specs. Specs are vectors
  describing a command line argument. For example:

  [\"-p\" \"--port\" \"Port to listen on\" :default 3000 :parse-fn #(Integer/parseInt %)]

  First provide the switches (from least to most specific), then a doc
  string, and pairs of options.

  Valid options are :default, :parse-fn, and :flag. See
  https://github.com/clojure/tools.cli/wiki/Documentation-for-0.2.4 for more
  detailed examples.

  Returns a vector containing a map of the parsed arguments, a vector
  of extra arguments that did not match known switches, and a
  documentation banner to provide usage instructions."
  [args & specs]
  (let [[desc specs] (if (string? (first specs))
                       [(first specs) (rest specs)]
                       [nil specs])
        specs (map generate-spec specs)
        args (normalize-args specs args)]
    (let [[options extra-args] (apply-specs specs args)
          banner  (with-out-str (banner-for desc specs))]
      [options extra-args banner])))

;;
;; New API
;;

(def ^{:private true} spec-keys
  [:id :short-opt :long-opt :required :desc :default :default-desc :parse-fn
   :assoc-fn :validate-fn :validate-msg])

(defn- select-spec-keys
  "Select only known spec entries from map and warn the user about unknown
   entries at development time."
  [map]
  ;; The following is formatted strangely for better manual diffing
  (when *assert*
    (let [unknown-keys (keys (apply dissoc map spec-keys))]
      (when (seq unknown-keys)
        (binding [*out* *err*]
          (println (str "Warning: The following options to parse-opts are unrecognized: "
                        (s/join ", " unknown-keys)))))
      ))
  (select-keys map spec-keys))

(defn- compile-spec [spec]
  (let [sopt-lopt-desc (take-while #(or (string? %) (nil? %)) spec)
        spec-map (apply hash-map (drop (count sopt-lopt-desc) spec))
        [short-opt long-opt desc] sopt-lopt-desc
        long-opt (or long-opt (:long-opt spec-map))
        [long-opt req] (when long-opt
                         (rest (re-find #"^(--[^ =]+)(?:[ =](.*))?" long-opt)))
        id (when long-opt
             (keyword (subs long-opt 2)))
        validate (:validate spec-map)
        [validate-fn validate-msg] (when (seq validate)
                                     (->> (partition 2 2 (repeat nil) validate)
                                          (apply map vector)))]
    (merge {:id id
            :short-opt short-opt
            :long-opt long-opt
            :required req
            :desc desc
            :validate-fn validate-fn
            :validate-msg validate-msg}
           (select-spec-keys (dissoc spec-map :validate)))))

(defn- distinct?* [coll]
  (if (seq coll)
    (apply distinct? coll)
    true))

(defn- wrap-val [map key]
  (if (contains? map key)
    (update-in map [key] #(cond (nil? %) nil
                                (coll? %) %
                                :else [%]))
    map))

(defn- compile-option-specs
  "Map a sequence of option specification vectors to a sequence of:

  {:id           Keyword  ; :server
   :short-opt    String   ; \"-s\"
   :long-opt     String   ; \"--server\"
   :required     String   ; \"HOSTNAME\"
   :desc         String   ; \"Remote server\"
   :default      Object   ; #<Inet4Address example.com/93.184.216.119>
   :default-desc String   ; \"example.com\"
   :parse-fn     IFn      ; #(InetAddress/getByName %)
   :assoc-fn     IFn      ; assoc
   :validate-fn  [IFn]    ; [#(instance? Inet4Address %)
                          ;  #(not (.isMulticastAddress %)]
   :validate-msg [String] ; [\"Must be an IPv4 host\"
                          ;  \"Must not be a multicast address\"]
   }

  :id defaults to the keywordized name of long-opt without leading dashes, but
  may be overridden in the option spec.

  The option spec entry `:validate [fn msg ...]` desugars into the two vector
  entries :validate-fn and :validate-msg. Multiple pairs of validation
  functions and error messages may be provided.

  A :default entry will not be included in the compiled spec unless specified.

  An option spec may also be passed as a map containing the entries above,
  in which case that subset of the map is transferred directly to the result
  vector.

  An assertion error is thrown if any :id values are unset, or if there exist
  any duplicate :id, :short-opt, or :long-opt values."
  [option-specs]
  {:post [(every? (comp identity :id) %)
          (distinct?* (map :id (filter :default %)))
          (distinct?* (remove nil? (map :short-opt %)))
          (distinct?* (remove nil? (map :long-opt %)))]}
  (map (fn [spec]
         (-> (if (map? spec)
               (select-spec-keys spec)
               (compile-spec spec))
             (wrap-val :validate-fn)
             (wrap-val :validate-msg)))
       option-specs))

(defn- default-option-map [specs]
  (reduce (fn [m s]
            (if (contains? s :default)
              (assoc m (:id s) (:default s))
              m))
          {} specs))

(defn- find-spec [specs opt-type opt]
  (first (filter #(= opt (opt-type %)) specs)))

(defn- pr-join [& xs]
  (pr-str (s/join \space xs)))

(defn- missing-required-error [opt example-required]
  (str "Missing required argument for " (pr-join opt example-required)))

(defn- parse-error [opt optarg msg]
  (str "Error while parsing option " (pr-join opt optarg) ": " msg))

(defn- validation-error [opt optarg msg]
  (str "Failed to validate " (pr-join opt optarg)
       (if msg (str ": " msg) "")))

(defn- validate [value spec opt optarg]
  (let [{:keys [validate-fn validate-msg]} spec]
    (or (loop [[vfn & vfns] validate-fn [msg & msgs] validate-msg]
          (when vfn
            (if (try (vfn value) (catch Throwable e))
              (recur vfns msgs)
              [::error (validation-error opt optarg msg)])))
        [value nil])))

(defn- parse-value [value spec opt optarg]
  (let [{:keys [parse-fn]} spec
        [value error] (if parse-fn
                        (try
                          [(parse-fn value) nil]
                          (catch Throwable e
                            [nil (parse-error opt optarg (str e))]))
                        [value nil])]
    (if error
      [::error error]
      (validate value spec opt optarg))))

(defn- parse-optarg [spec opt optarg]
  (let [{:keys [required]} spec]
    (if (and required (nil? optarg))
      [::error (missing-required-error opt required)]
      (parse-value (if required optarg true) spec opt optarg))))

(defn- parse-option-tokens
  "Reduce sequence of [opt-type opt ?optarg?] tokens into a map of
  {option-id value} merged over the default values in the option
  specifications.

  If the :no-defaults flag is true, only options specified in the tokens are
  included in the option-map.

  Unknown options, missing required arguments, option argument parsing
  exceptions, and validation failures are collected into a vector of error
  message strings.

  Returns [option-map error-messages-vector]."
  [specs tokens & options]
  (let [{:keys [no-defaults]} (apply hash-map options)
        defaults (default-option-map specs)]
    (-> (reduce
          (fn [[m ids errors] [opt-type opt optarg]]
            (if-let [spec (find-spec specs opt-type opt)]
              (let [[value error] (parse-optarg spec opt optarg)
                    id (:id spec)]
                (if-not (= value ::error)
                  [((:assoc-fn spec assoc) m id value) (conj ids id) errors]
                  [m ids (conj errors error)]))
              [m ids (conj errors (str "Unknown option: " (pr-str opt)))]))
          [defaults [] []] tokens)
        (#(let [[m ids errors] %]
            (if no-defaults
              [(select-keys m ids) errors]
              [m errors]))))))

(defn- make-summary-parts [show-defaults? specs]
  (let [{:keys [short-opt long-opt required default default-desc desc]} specs
        opt (cond (and short-opt long-opt) (str short-opt ", " long-opt)
                  long-opt (str "    " long-opt)
                  short-opt short-opt)
        [opt dd] (if required
                   [(str opt \space required)
                    (or default-desc (str default))]
                   [opt ""])]
    (if show-defaults?
      [opt dd (or desc "")]
      [opt (or desc "")])))

(defn- format-lines [lens parts]
  (let [fmt (case (count lens)
              2 "~{  ~vA  ~vA~}"
              3 "~{  ~vA  ~vA  ~vA~}")]
    (map #(s/trimr (pp/cl-format nil fmt (interleave lens %))) parts)))

(defn- required-arguments [specs]
  (reduce
    (fn [s {:keys [required short-opt long-opt]}]
      (if required
        (into s (remove nil? [short-opt long-opt]))
        s))
    #{} specs))

(defn ^{:added "0.3.0"} summarize
  "Reduce options specs into a options summary for printing at a terminal."
  [specs]
  (if (seq specs)
    (let [show-defaults? (some #(and (:required %) (contains? % :default)) specs)
          parts (map (partial make-summary-parts show-defaults?) specs)
          lens (apply map (fn [& cols] (apply max (map count cols))) parts)
          lines (format-lines lens parts)]
      (s/join \newline lines))
    ""))

(defn ^{:added "0.3.2"} get-default-options
  "Extract the map of default options from a sequence of option vectors."
  [option-specs]
  (default-option-map (compile-option-specs option-specs)))

(defn ^{:added "0.3.0"} parse-opts
  "Parse arguments sequence according to given option specifications and the
  GNU Program Argument Syntax Conventions:

    https://www.gnu.org/software/libc/manual/html_node/Argument-Syntax.html

  Option specifications are a sequence of vectors with the following format:

    [short-opt long-opt-with-required-description description
     :property value]

  The first three string parameters in an option spec are positional and
  optional, and may be nil in order to specify a later parameter.

  By default, options are toggles that default to nil, but the second string
  parameter may be used to specify that an option requires an argument.

    e.g. [\"-p\" \"--port PORT\"] specifies that --port requires an argument,
         of which PORT is a short description.

  The :property value pairs are optional and take precedence over the
  positional string arguments. The valid properties are:

    :id           The key for this option in the resulting option map. This
                  is normally set to the keywordized name of the long option
                  without the leading dashes.

                  Multiple option entries can share the same :id in order to
                  transform a value in different ways, but only one of these
                  option entries may contain a :default entry.

                  This option is mandatory.

    :short-opt    The short format for this option, normally set by the first
                  positional string parameter: e.g. \"-p\". Must be unique.

    :long-opt     The long format for this option, normally set by the second
                  positional string parameter; e.g. \"--port\". Must be unique.

    :required     A description of the required argument for this option if
                  one is required; normally set in the second positional
                  string parameter after the long option: \"--port PORT\".

                  The absence of this entry indicates that the option is a
                  boolean toggle that is set to true when specified on the
                  command line.

    :desc         A optional short description of this option.

    :default      The default value of this option. If none is specified, the
                  resulting option map will not contain an entry for this
                  option unless set on the command line.

    :default-desc An optional description of the default value. This should be
                  used when the string representation of the default value is
                  too ugly to be printed on the command line.

    :parse-fn     A function that receives the required option argument and
                  returns the option value.

                  If this is a boolean option, parse-fn will receive the value
                  true. This may be used to invert the logic of this option:

                  [\"-q\" \"--quiet\"
                   :id :verbose
                   :default true
                   :parse-fn not]

    :assoc-fn     A function that receives the current option map, the current
                  option :id, and the current parsed option value, and returns
                  a new option map.

                  This may be used to create non-idempotent options, like
                  setting a verbosity level by specifying an option multiple
                  times. (\"-vvv\" -> 3)

                  [\"-v\" \"--verbose\"
                   :default 0
                   :assoc-fn (fn [m k _] (update-in m [k] inc))]

    :validate     A vector of [validate-fn validate-msg ...]. Multiple pairs
                  of validation functions and error messages may be provided.

    :validate-fn  A vector of functions that receives the parsed option value
                  and returns a falsy value or throws an exception when the
                  value is invalid. The validations are tried in the given
                  order.

    :validate-msg A vector of error messages corresponding to :validate-fn
                  that will be added to the :errors vector on validation
                  failure.

  parse-opts returns a map with four entries:

    {:options     The options map, keyed by :id, mapped to the parsed value
     :arguments   A vector of unprocessed arguments
     :summary     A string containing a minimal options summary
     :errors      A possible vector of error message strings generated during
                  parsing; nil when no errors exist}

  A few function options may be specified to influence the behavior of
  parse-opts:

    :in-order     Stop option processing at the first unknown argument. Useful
                  for building programs with subcommands that have their own
                  option specs.

    :no-defaults  Only include option values specified in arguments and do not
                  include any default values in the resulting options map.
                  Useful for parsing options from multiple sources; i.e. from a
                  config file and from the command line.

    :summary-fn   A function that receives the sequence of compiled option specs
                  (documented at #'clojure.tools.cli/compile-option-specs), and
                  returns a custom option summary string.
  "
  [args option-specs & options]
  (let [{:keys [in-order no-defaults summary-fn]} (apply hash-map options)
        specs (compile-option-specs option-specs)
        req (required-arguments specs)
        [tokens rest-args] (tokenize-args req args :in-order in-order)
        [opts errors] (parse-option-tokens
                        specs tokens :no-defaults no-defaults)]
    {:options opts
     :arguments rest-args
     :summary ((or summary-fn summarize) specs)
     :errors (when (seq errors) errors)}))
