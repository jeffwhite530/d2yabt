#!/usr/bin/env python3
"""This file contains the functions which are performed on a DC/OS bundle.
"""



import sys
import os
import re
import pandas
import d2yabt



def extract_diag(bundle_name):
	"""Expand the DC/OS bundle into a directory.
	"""
	bundle_name = d2yabt.util.relocate_bundle(bundle_name)
	bundle_dir = d2yabt.util.get_bundle_dir(bundle_name)

	print("Extracting DC/OS diagnostic bundle to", bundle_dir)

	d2yabt.util.unzip(bundle_name, bundle_dir)

	return bundle_dir



def extract_oneliner(bundle_name):
	"""Expand the oneliner bundle into a directory.
	"""
	bundle_name = d2yabt.util.relocate_bundle(bundle_name)
	bundle_dir = d2yabt.util.get_bundle_dir(bundle_name)

	print("Extracting DC/OS oneliner bundle to", bundle_dir)

	d2yabt.util.untar(bundle_name, bundle_dir)

	return bundle_dir



def get_nodes(bundle_dir, bundle_type):
	"""Get the list of nodes and create an object for each.
	"""
	print("Obtaining list of nodes")

	node_objs = list()

	if bundle_type == "dcos_diag":
		for node_dir in os.listdir(bundle_dir):
			if not os.path.isdir(os.path.join(bundle_dir, node_dir)):
				continue

			node_obj = d2yabt.Node()
			node_obj.dir = os.path.join(bundle_dir, node_dir)

			if node_dir.endswith("_master"):
				node_obj.type = "master"

			elif node_dir.endswith("_agent"):
				node_obj.type = "priv_agent"

			elif node_dir.endswith("_agent_public"):
				node_obj.type = "pub_agent"

			node_obj.ip = node_dir.split("_")[0]

			node_objs.append(node_obj)

	elif bundle_type == "dcos_oneliner":
		node_obj = d2yabt.Node()

		node_obj.dir = bundle_dir
		node_obj.ip = "unknown"

		if os.path.exists(os.path.join(bundle_dir, "dcos-mesos-master.service.log")):
			node_obj.type = "master"

		elif os.path.exists(os.path.join(bundle_dir, "dcos-mesos-slave.service.log")):
			node_obj.type = "priv_agent"

		elif os.path.exists(os.path.join(bundle_dir, "dcos-mesos-slave-public.service.log")):
			node_obj.type = "pub_agent"

		node_objs.append(node_obj)


	if not node_objs:
		print("Failed to find any nodes in the bundle directory", file=sys.stderr)
		sys.exit(1)

	return node_objs



def get_node_info(node_objs):
	"""Gather information about DC/OS nodes.
	"""
	for node_obj in node_objs:
		# Get the Docker version
		if node_obj.type == "master":
			node_obj.docker_version = "n/a"

		else:
			if os.path.exists(os.path.join(node_obj.dir, "docker_--version.output")):
				docker_version_text = open(os.path.join(node_obj.dir, "docker_--version.output"), "r").read()

				docker_version = re.search(r"Docker version (.*),", docker_version_text).group(1)

				node_obj.docker_version = docker_version

			else:
				node_obj.docker_version = "unknown"

		# Get the OS
		if os.path.exists(os.path.join(node_obj.dir, "binsh_-c_cat etc*-release.output")):
			os_file_text = open(os.path.join(node_obj.dir, "binsh_-c_cat etc*-release.output"), "r").read()

			node_os = re.search(r'ID="(.*)"', os_file_text).group(1)
			node_obj.os = node_os

		else:
			node_obj.os = "unkown"



def print_nodes(node_objs):
	"""Prints a table of nodes.
	"""
	node_table = pandas.DataFrame(data={
			"IP": [o.ip for o in node_objs],
			"Type": [o.type for o in node_objs],
			"OS": [o.os for o in node_objs],
			"Docker": [o.docker_version for o in node_objs],
		}
	)

	node_table.sort_values("Type", inplace=True)
	node_table.reset_index(inplace=True, drop=True)
	node_table.index += 1

	print(node_table)

