#!/usr/bin/env python3
"""This file contains the functions which are performed on a service bundle.
"""



import d2yabt



def extract(bundle_name):
	"""Expand the service bundle into a directory.
	"""
	bundle_name = d2yabt.util.relocate_bundle(bundle_name)
	bundle_dir = d2yabt.util.get_bundle_dir(bundle_name)

	print("Extracting service bundle to", bundle_dir)

	d2yabt.util.unzip(bundle_name, bundle_dir)

	return bundle_dir

