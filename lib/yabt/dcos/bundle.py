#!/usr/bin/env python3



# pylint: disable=line-too-long



import yabt
import sys
import os
import zipfile
import shutil
import re
import pandas
import tarfile
import subprocess



def extract_diag(bundle_name):
	"""Expand the DC/OS bundle into a directory.
	"""

	bundle_name_base = os.path.basename(bundle_name)

	if not bundle_name == bundle_name_base:
		os.rename(bundle_name, bundle_name_base)

		print("Moved", bundle_name_base, "to the current working directory")

		bundle_name = bundle_name_base

	bundle_dir = yabt.util.get_bundle_dir(bundle_name)

	print("Extracting DC/OS diagnostic bundle to", bundle_dir)

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



def extract_oneliner(bundle_name):
	"""Expand the oneliner bundle into a directory.
	"""

	bundle_name_base = os.path.basename(bundle_name)

	if not bundle_name == bundle_name_base:
		os.rename(bundle_name, bundle_name_base)

		print("Moved", bundle_name_base, "to the current working directory")

		bundle_name = bundle_name_base

	bundle_dir = yabt.util.get_bundle_dir(bundle_name)

	print("Extracting DC/OS oneliner bundle to", bundle_dir)

	tarfile_obj = tarfile.open(bundle_name, "r:gz")

	tarfile_obj.extractall(bundle_dir)

	tarfile_obj.close()

	return bundle_dir



def get_nodes(bundle_dir, bundle_type):
	"""Get the list of nodes and create an object for each.
	"""
	print("Obtaining list of nodes")

	node_objs = list()

	if bundle_type == "dcos_diag":
		for node_dir in os.listdir(bundle_dir):
			if not os.path.isdir(bundle_dir + os.sep + node_dir):
				continue

			node_obj = yabt.Node()
			node_obj.dir = bundle_dir + os.sep + node_dir

			if node_dir.endswith("_master"):
				node_obj.ip = node_dir[:-7]
				node_obj.type = "master"

			elif node_dir.endswith("_agent"):
				node_obj.ip = node_dir[:-6]
				node_obj.type = "priv_agent"

			elif node_dir.endswith("_agent_public"):
				node_obj.ip = node_dir[:-13]
				node_obj.type = "pub_agent"

			node_objs.append(node_obj)

	elif bundle_type == "dcos_oneliner":
		node_obj = yabt.Node()

		node_obj.dir = bundle_dir

		node_obj.ip = "unknown"

		if os.path.exists(bundle_dir + os.sep + "dcos-mesos-master.service.log"):
			node_obj.type = "master"

		elif os.path.exists(bundle_dir + os.sep + "dcos-mesos-slave.service.log"):
			node_obj.type = "priv_agent"

		elif os.path.exists(bundle_dir + os.sep + "dcos-mesos-slave-public.service.log"):
			node_obj.type = "pub_agent"

		node_objs.append(node_obj)


	if len(node_objs) == 0:
		print("Failed to find any nodes in the bundle directory", file=sys.stderr)

		sys.exit(1)

	return node_objs



def print_nodes(node_objs):
	"""Prints a table of nodes.
	"""
	node_table = pandas.DataFrame(data = {
			"IP": [o.ip for o in node_objs],
			"Type": [o.type for o in node_objs],
		}
	)

	node_table.sort_values("Type", inplace=True)

	node_table.reset_index(inplace=True, drop=True)

	node_table.index += 1

	print(node_table)

