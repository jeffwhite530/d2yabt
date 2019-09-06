#!/usr/bin/env python3



import sys
import os
import re
import pandas
import yabt



def extract(bundle_name):
	"""Expand the Konvoy bundle into a directory.
	"""

	bundle_name_base = os.path.basename(bundle_name)

	if not bundle_name == bundle_name_base:
		os.rename(bundle_name, bundle_name_base)

		print("Moved", bundle_name_base, "to the current working directory")

		bundle_name = bundle_name_base

	bundle_dir = yabt.util.get_bundle_dir(bundle_name)

	print("Extracting Konvoy bundle to", bundle_dir)

	yabt.util.untar(bundle_name, bundle_dir)

	for root, dirs, files in os.walk(bundle_dir):
		for each_file in files:
			if not each_file.endswith(".tar.gz"):
				continue

			file_with_path = root + os.sep + each_file

			file_with_path_no_ext = file_with_path[:-7]

			yabt.util.untar(file_with_path, file_with_path_no_ext)

	return bundle_dir



def get_nodes(bundle_dir):
	"""Get the list of nodes and create an object for each.
	"""
	print("Obtaining list of nodes")

	node_objs = list()

	for node_dir in os.listdir(bundle_dir + os.sep + "bundles"):
		if not os.path.isdir(bundle_dir + os.sep + "bundles" + os.sep + node_dir):
			continue

		if re.search(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", node_dir) is None:
			continue

		node_obj = yabt.Node()

		node_obj.dir = bundle_dir + os.sep + node_dir
		node_obj.ip = node_dir
		node_obj.type = "Konvoy kubelet"

		node_objs.append(node_obj)
	
	if not node_objs:
		print("Failed to find any nodes in the bundle directory", file=sys.stderr)

		sys.exit(1)

	return node_objs



def print_nodes(node_objs):
	"""Prints a table of nodes.
	"""
	node_table = pandas.DataFrame(data={
			"IP": [o.ip for o in node_objs],
			"Type": [o.type for o in node_objs]
		}
	)

	node_table.index += 1

	print(node_table)

