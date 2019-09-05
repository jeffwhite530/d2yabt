#!/usr/bin/env python3



# pylint: disable=line-too-long



import sys
import os
import zipfile
import subprocess
import shutil
import yabt



def extract(bundle_name):
	"""Expand the service bundle into a directory.
	"""

	bundle_name_base = os.path.basename(bundle_name)

	if not bundle_name == bundle_name_base:
		os.rename(bundle_name, bundle_name_base)

		print("Moved", bundle_name_base, "to the current working directory")

		bundle_name = bundle_name_base

	bundle_dir = yabt.util.get_bundle_dir(bundle_name)

	print("Extracting service bundle to", bundle_dir)

	os.mkdir(bundle_dir)

	try:
		zip_ref = zipfile.ZipFile(bundle_name, "r")
		zip_ref.extractall(bundle_dir)
		zip_ref.close()

	except zipfile.BadZipFile:
		print("Failed to extract bundle, corrupt zip?  Attempting to extract with 7zip", file=sys.stderr)

		zip7_command = shutil.which("7z")

		if zip7_command is None:
			print("7zip command (7z) not found.  Please install 7zip.", file=sys.stderr)

			sys.exit(1)

		zip7_process = subprocess.Popen([zip7_command, "x", "-o" + bundle_dir, "-y", bundle_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		zip7_process.wait()

		# Note that we're not checking if 7zip was successful because it will exit non-zero even if it was able to partially extract the zip.

	# If the extracted bundle is within a directory, move the contents of that directory up one
	bundle_contents = os.listdir(bundle_dir)

	if len(bundle_contents) == 1:
		for each in os.listdir(bundle_dir + os.sep + bundle_contents[0]):
			os.rename(bundle_dir + os.sep + bundle_contents[0] + os.sep + each, bundle_dir + os.sep + each)

		os.rmdir(bundle_dir + os.sep + bundle_contents[0])

	return bundle_dir

