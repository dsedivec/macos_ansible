#!/bin/sh

macports_python=/opt/local/bin/python2.7
result=/usr/bin/python
if [ -x "$macports_python" ] &&
	   "$macports_python" -c "import CoreFoundation" >/dev/null 2>&1
then
	result=$macports_python
fi

echo "$result"
