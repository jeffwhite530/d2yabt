#!/bin/bash

# Run tests on yabt to ensure it works as expected

set -e

test_bundles_dir="${HOME}/yabt/test-bundles"

working_dir=$(mktemp -d)

echo "Working in temp directory $working_dir"

cd "$working_dir"


echo "Testing a Konvoy bundle"

cp ${test_bundles_dir}/konvoy/konvoy-diag.tar.gz .

echo "	Extract and examine ..."
yabt konvoy-diag.tar.gz >/dev/null

echo "	Detect existing dir and examine ..."
yabt konvoy-diag.tar.gz >/dev/null

echo "	Use existing dir and examine ..."
yabt konvoy-diag >/dev/null


echo "Testing a service bundle"

cp ${test_bundles_dir}/service/service_diag.zip .

echo "	Extract and examine ..."
yabt service_diag.zip >/dev/null

echo "	Detect existing dir and examine ..."
yabt service_diag.zip >/dev/null

echo "	Use and existing dir and examine ..."
#yabt service_diag >/dev/null


echo "Testing a DC/OS 1.13 diagnostic bundle"

cp ${test_bundles_dir}/dcos/diag/bundle-test-1-13-3.zip .

echo "	Extract and examine ..."
yabt bundle-test-1-13-3.zip >/dev/null

echo "	Detect existing dir and examine ..."
yabt bundle-test-1-13-3.zip >/dev/null

echo "	Use existing dir and examine ..."
yabt bundle-test-1-13-3 >/dev/null


echo "Testing a DC/OS 1.12 diagnostic bundle"

cp ${test_bundles_dir}/dcos/diag/bundle-test-1-12-3.zip .

echo "	Extract and examine ..."
yabt bundle-test-1-12-3.zip >/dev/null

echo "	Detect existing dir and examine ..."
yabt bundle-test-1-12-3.zip >/dev/null

echo "	Use existing dir and examine ..."
yabt bundle-test-1-12-3 >/dev/null


echo "Testing a DC/OS 1.11 diagnostic bundle"

cp ${test_bundles_dir}/dcos/diag/bundle-test-1-11-10.zip .

echo "	Extract and examine ..."
yabt bundle-test-1-11-10.zip >/dev/null

echo "	Detect existing dir and examine ..."
yabt bundle-test-1-11-10.zip >/dev/null

echo "	Use existing dir and examine ..."
yabt bundle-test-1-11-10 >/dev/null


echo "Testing a DC/OS 1.11 diagnostic bundle in a different directory"

rm -rf bundle-test-1-11-10.zip bundle-test-1-11-10

test_dir=$(mktemp -d)

cp ${test_bundles_dir}/dcos/diag/bundle-test-1-11-10.zip ${test_dir}/

yabt ${test_dir}/bundle-test-1-11-10.zip >/dev/null

[ -d bundle-test-1-11-10 ] || echo "Failure!"
[ -f bundle-test-1-11-10.zip ] || echo "Failure!"


echo "Testing a DC/OS oneliner bundle"

cp ${test_bundles_dir}/dcos/oneliner/bundle-oneliner.tgz .

echo "	Extract and examine ..."
yabt bundle-oneliner.tgz >/dev/null

echo "	Detect existing dir and examine ..."
yabt bundle-oneliner.tgz >/dev/null

echo "	Use existing dir and examine ..."
yabt bundle-oneliner >/dev/null


echo "All test were successfull!"

echo "Removing temp directory $working_dir"

rm -rf "$working_dir"

