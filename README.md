yabt (Yet Another Bundle Tool) is used to analyze [DC/OS diagnostic bundles](https://support.d2iq.com/s/article/Create-a-DC-OS-Diagnostic-bundle), [DC/OS service diagnostic bundles](https://support.d2iq.com/s/article/create-service-diag-bundle), and [Konvoy diagnostic bundles](https://docs.d2iq.com/ksphere/konvoy/latest/troubleshooting/generate-diagnostic-bundle).  It performs many of the same functions as [Andrey Dyatlov's](https://github.com/adyatlov) [bun](https://github.com/adyatlov/bun/releases) and [Dustin Nemes'](https://github.com/some-things) [dcosqj](https://github.com/some-things/dcosjq).  Essentially it does two things:

1. Decompresses the bundle and the files within it
2. Reads JSON and log files to find common problems and warns about them

### To run
First, you'll need to install yabt's dependencies:
```
pip3 install pandas
```

Assuming yabt is in your home directory, you'll need to adjust PYTHONPATH so it can find the library like so:
```
PYTHONPATH=$PYTHONPATH:~/yabt/lib ~/yabt/bin/yabt path/to/bundle.zip
```

yabt will extract the bundle to the current working directory and move the bundle file to the current directory as well.  It then runs through the health checks available for that specific bundle type.  You can also run yabt with no argument to use the current directory as the bundle:
```
cd path/to/bundle
PYTHONPATH=$PYTHONPATH:~/yabt/lib ~/yabt/bin/yabt
```

### To add checks

yabt was designed to be easy to extended and have a simple to understand architecture.  Each supported bundle type is broken into its own namespace:
```
DC/OS --> yabt.dcos
Service --> yabt.service
Konvoy --> yabt.konvoy
```

Each of those has a "check" library where health checks are defined.  These map to the following files:
```
yabt.dcos.check --> lib/yabt/dcos/check.py
yabt.service.check --> lib/yabt/service/check.py
yabt.konvoy.check --> lib/yabt/konvoy/check.py
```

To add a check, add a function to the appropriate file.  Have that function do anything you want (search a log file, parse a JSON/YAML file, etc.).  Then simply add a call to that function in bin/yabt in the section labeled '# Health checks'.

