#!/usr/bin/env python3



# pylint: disable=line-too-long



import sys
import os
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

	yabt.util.unzip(bundle_name, bundle_dir)

	return bundle_dir

