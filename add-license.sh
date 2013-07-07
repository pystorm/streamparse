#!/bin/bash
# based on http://stackoverflow.com/a/151690/105571

find . -name  "*.py" | while read i
do
  if ! grep -q Copyright $i
  then
    echo '__license__ = """' > $i.new
    cat LICENSE | tail -13 >> $i.new
    echo '"""' >> $i.new
    echo '' >> $i.new
    cat $i >> $i.new
    mv $i.new $i
  fi
done
