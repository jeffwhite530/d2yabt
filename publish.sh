#!/bin/bash

rm -rf build dist d2yabt.egg-info/
docker image rm jwhitemeso/d2yabt:latest

PYTHONPATH=$PYTHONPATH:~/d2yabt/lib python3 setup.py sdist bdist_wheel || exit 1

python3 -m twine upload --verbose --repository-url https://upload.pypi.org/legacy/ dist/*

docker build -t jwhitemeso/d2yabt:latest - <<EOF
FROM ubuntu:latest
RUN apt update && apt -y install python3 python3-pip p7zip-full
RUN pip3 install --no-cache-dir d2yabt
CMD ["/bin/bash"]
EOF

docker push jwhitemeso/d2yabt:latest

