d2yabt (Yet Another Bundle Tool) is used to analyze [DC/OS diagnostic bundles](https://support.d2iq.com/s/article/Create-a-DC-OS-Diagnostic-bundle), [DC/OS service diagnostic bundles](https://support.d2iq.com/s/article/create-service-diag-bundle), and [Konvoy diagnostic bundles](https://docs.d2iq.com/ksphere/konvoy/latest/troubleshooting/generate-diagnostic-bundle).  It performs many of the same functions as [Andrey Dyatlov's](https://github.com/adyatlov) [bun](https://github.com/adyatlov/bun/releases) and [Dustin Nemes'](https://github.com/some-things) [dcosqj](https://github.com/some-things/dcosjq).  Essentially it does two things:

1. Decompresses the bundle and the files within it
2. Reads JSON and log files to find common problems and warns about them

### To install
d2yabt is on PyPI so install it via pip:
```
pip3 install d2yabt
```

### To run
d2yabt's executable is `yabt`.  Run it with a bundle as the argument and d2yabt will extract the bundle to the current working directory and move the bundle file to the current directory:
```
yabt path/to/bundle.zip
```

d2yabt can also be used on an extracted bundle.  Either give it the path to the bundle directory as an argument or cd into it and run yabt with no arguments:
```
cd path/to/bundle
yabt
```

Note that pip will install d2yabt to wherever your user base is set to.  You'll need to add its bin directory to your PATH:
```
export PATH="$PATH:$(python3 -m site --user-base)/bin"
```

### Manual install (via git)
First, you'll need to install d2yabt's dependencies:
```
pip3 install pandas
```

Next, clone the repo:
```
git clone git@github.com:jeffwhite530/d2yabt.git
```

Finally, adjust PYTHONPATH so Python can find the library.  Assuming d2yabt is in your home directory, run it like so:
```
PYTHONPATH=$PYTHONPATH:~/d2yabt/lib ~/d2yabt/bin/yabt path/to/bundle.zip
```

### To add checks

d2yabt was designed to be easy to extended and have a simple to understand architecture.  Each supported bundle type is broken into its own namespace:
```
DC/OS --> d2yabt.dcos
Service --> d2yabt.service
Konvoy --> d2yabt.konvoy
```

Each of those has a "check" library where health checks are defined.  These map to the following files:
```
d2yabt.dcos.check --> lib/d2yabt/dcos/check.py
d2yabt.service.check --> lib/d2yabt/service/check.py
d2yabt.konvoy.check --> lib/d2yabt/konvoy/check.py
```

To add a check, add a function to the appropriate check.py file.  Have that function do anything you want (search a log file, parse a JSON/YAML file, etc.).  Then simply add a call to that function in bin/yabt in the section labeled '# Health checks'.

