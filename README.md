yabt (Yet Another Bundle Tool) is used to analyze [DC/OS diagnostic bundles](https://support.mesosphere.com/s/article/Create-a-DC-OS-Diagnostic-bundle).  It performs many of the same functions as [Andrey Dyatlov's](https://github.com/adyatlov) [bun](https://github.com/adyatlov/bun/releases) and [Dustin Nemes'](https://github.com/some-things) [dcosqj](https://github.com/some-things/dcosjq).  Essentially it does two things:

1. Decompresses the bundle (also supports one-liner bundles; service diagnostic bundle support is TODO)
2. Reads JSON and log files to find common problems and warns about them

### To add checks

yabt was designed to be easily extended and have a simple to understand architecture.  To add a check, add a function to lib/yabt/check.py that does anything you want it to do.  Then simply add a call to that function in bin/yabt.

