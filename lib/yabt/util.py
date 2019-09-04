#!/usr/bin/env python3



# pylint: disable=line-too-long



import yabt
import sys
import os
import argparse
import gzip
import shutil
import json
import re
import signal
import glob
import zipfile
import tarfile



def decompress_gzip_files(start_dir):
	"""Walk a directory tree and decompress all gzip files found.
	"""
	print("Expanding bundle files")

	for root, dirs, files in os.walk(start_dir):
		for each_file in files:
			if not each_file.endswith(".gz"):
				continue

			file_with_path = root + os.sep + each_file

			file_with_path_no_ext = file_with_path[:-3]

			try:
				with gzip.open(file_with_path, "rb") as f_in:
					with open(file_with_path_no_ext, "wb") as f_out:
						shutil.copyfileobj(f_in, f_out)

			except EOFError:
				print("Failed to expand", file_with_path, "EOF reached, incomplete file?")

			except OSError:
				print("Failed to expand", file_with_path + ", not a gzip file?")

			else:
				os.remove(file_with_path)



def format_json(bundle_dir):
	"""Format the JSON files into a human-readable form.
	"""
	print("Formatting JSON files")

	for root, dirs, files in os.walk(bundle_dir):
		for each_file in files:
			if not each_file.endswith(".json"):
				continue

			# This file always fails to parse, just skip it
			if each_file == "443-licensing_v1_audit_decrypt_1.json":
				continue

			file_with_path = root + os.sep + each_file

			with open(file_with_path, "r+") as json_file_handle:
				try:
					json_data = json.load(json_file_handle)

					json_file_handle.seek(0)

					json_file_handle.write(json.dumps(json_data, indent=2, sort_keys=True))
					json_file_handle.write("\n")

				except (json.decoder.JSONDecodeError, UnicodeDecodeError):
					print("Failed to parse JSON:", file_with_path, file=sys.stderr)



def get_bundle_type(bundle_name):
	"""Determine the type of bundle given and return a string of either:
		* dcos_diag
		* dcos_oneliner
		* service_diag
		* konvoy_diag
	"""

	if os.path.isdir(bundle_name):
		if glob.glob(bundle_name + os.sep + "*_master/dcos-mesos-master.service"):
			return "dcos_diag"

		if glob.glob(bundle_name + os.sep + "dcos-mesos-master.service.log"):
			return "dcos_oneliner"

		if glob.glob(bundle_name + os.sep + "dcos-mesos-slave*.service.log"):
			return "dcos_oneliner"

		if glob.glob(bundle_name + os.sep + "dcos_services.json"):
			return "service_diag"

	elif os.path.isfile(bundle_name):
		if bundle_name.endswith(".zip"):
			myzip = zipfile.ZipFile(bundle_name)

			for each in myzip.namelist():
				if each.endswith("_master/dcos-mesos-master.service.gz"):
					return "dcos_diag"

				if each.endswith("dcos_services.json"):
					return "service_diag"

		if bundle_name.endswith(".tgz") or bundle_name.endswith(".tar.gz"):
			mytar = tarfile.open(bundle_name, "r:gz")

			for each in mytar.getmembers():
				if each.name.endswith("dcos-mesos-master.service.log"):
					return "dcos_oneliner"

				if each.name.endswith("dcos-mesos-slave.service.log"):
					return "dcos_oneliner"

				if each.name.endswith("dcos-mesos-slave-public.service.log"):
					return "dcos_oneliner"

				if each.name.startswith("bundles/"):
					return "konvoy_diag"

	print("Unable to determine bundle type", file=sys.stderr)

	sys.exit(1)



def get_bundle_dir(bundle_name):
	"""Parse the bundle directory from the bundle name.
	"""
	if os.path.isdir(bundle_name):
		return bundle_name

	elif bundle_name.endswith(".tgz") or bundle_name.endswith(".zip"):
		return bundle_name[:-4]

	elif bundle_name.endswith(".tar.gz"):
		return bundle_name[:-7]

	else:
		print("Unable to parse bundle name", file=sys.stderr)

		sys.exit(1)



def is_bundle_extracted(bundle_name):
	"""Checks if the named bundle is already extracted.
		If yes: return True
		If no: return False
	"""
	bundle_dir = get_bundle_dir(bundle_name)

	if os.path.exists(bundle_dir):
		return True

	else:
		return False

