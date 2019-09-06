#!/usr/bin/env python3



import sys
import os
import yabt



def extract(bundle_name):
	"""Expand the service bundle into a directory.
	"""
	bundle_name = yabt.util.relocate_bundle(bundle_name)
	bundle_dir = yabt.util.get_bundle_dir(bundle_name)

	print("Extracting service bundle to", bundle_dir)

	yabt.util.unzip(bundle_name, bundle_dir)

	return bundle_dir

