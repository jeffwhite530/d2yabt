#!/usr/bin/env python3



# pylint: disable=line-too-long



import sys
import os
import shutil
import json
import re
import pandas



pandas.options.display.max_colwidth=200


def dcos_version(node_objs):
	"""Check that all nodes are using the same DC/OS version.
	"""
	print("Checking for DC/OS version mismatch")

	dcos_versions_list = list()

	for node_obj in node_objs:
		try:
			with open(node_obj.dir + "/opt/mesosphere/etc/dcos-version.json", "r") as json_file:
				version_json = json.load(json_file)

			node_obj.dcos_version = version_json["version"]

			dcos_versions_list.append(node_obj.dcos_version)

		except FileNotFoundError:
			print("WARNING: No dcos-version.json file found for node", node_obj.ip)

			continue

	dcos_versions_set = set(dcos_versions_list)


	# Print the node table
	if not len(dcos_versions_set) == 1:
		print("WARNING: Found non-matching DC/OS versions!")

		node_table = pandas.DataFrame(data = {
				"IP": [o.ip for o in node_objs],
				"Type": [o.type for o in node_objs],
				"DC/OS Version": [o.dcos_version for o in node_objs]
			}
		)

		node_table.sort_values("DC/OS Version", inplace=True)

		node_table.reset_index(inplace=True, drop=True)

		node_table.index += 1

		print(node_table)



def firewall_running(node_objs):
	"""Check to see if firewalld is running.
	"""
	print("Checking for running firewall")

	firewall_node_objs = list()

	for node_obj in sorted(node_objs, key=lambda x: x.type):
		if not os.path.exists(node_obj.dir + os.sep + "ps_aux_ww_Z.output"):
			print("Unable to check for running firewall: No ps output available")

			break

		with open(node_obj.dir + os.sep + "ps_aux_ww_Z.output", "r") as ps_file:
			for each_line in ps_file:
				each_line = each_line.rstrip("\n")

				if re.search("firewalld", each_line) is not None:
					node_obj.firewalld_running = True

					firewall_node_objs.append(node_obj)

	# Print the node table
	if not len(firewall_node_objs) == 0:
		node_table = pandas.DataFrame(data = {
				"IP": [o.ip for o in firewall_node_objs],
				"Type": [o.type for o in firewall_node_objs],
				"firewalld": [o.firewalld_running for o in firewall_node_objs]
			}
		)

		node_table.sort_values("firewalld", inplace=True)

		node_table.reset_index(inplace=True, drop=True)

		node_table.index += 1

		print(node_table)



def missing_agents(node_objs):
	"""Check for agents which are unreachable according to the Mesos master and for agent which are not in the bundle.
	"""
	print("Checking for missing agents")

	unreachable_nodes = dict()

	for node_obj in node_objs:
		if not node_obj.type == "master":
			continue

		if os.path.exists(node_obj.dir + os.sep + "dcos-mesos-master.service"):
			mesos_log = node_obj.dir + os.sep + "dcos-mesos-master.service"

		elif os.path.exists(node_obj.dir + os.sep + "dcos-mesos-master.service.log"):
			mesos_log = node_obj.dir + os.sep + "dcos-mesos-master.service.log"

		with open(mesos_log, "r") as mesos_master_log:
			for each_line in mesos_master_log:
				each_line = each_line.rstrip("\n")

				if re.search("Marking agent.*unreachable", each_line) is None:
					continue

				match = re.search("^([^\s]+).*(\d+:\d+:\d+\.\d+).*Marking agent.*\((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\) unreachable", each_line)

				if match is not None:
					unreachable_nodes[match.group(1) + " " + match.group(2)] = match.group(3)

	if not len(unreachable_nodes) == 0:
		print("WARNING: Unreachable agents found:")

	unreachable_ips = list()

	for timestamp, ip in unreachable_nodes.items():
		print("\t", timestamp + ":", ip)

		unreachable_ips.append(ip)

	unreachable_ips = set(unreachable_ips)

	for unreachable_ip in sorted(unreachable_ips):
		if not any(x.ip == unreachable_ip for x in node_objs):
			print("WARNING: Agent found in Mesos master log but not in the bundle:", unreachable_ip)



def time_sync(node_objs):
	"""Check if any time sync errors have occured.
	"""
	print("Checking for time sync errors")

	check_time_error_node_objs = list()

	for node_obj in node_objs:
		for file_name in os.listdir(node_obj.dir):
			# If we already found a check-time error on this node, move on to the next one
			if node_obj in check_time_error_node_objs:
				break

			if not file_name.endswith(".service"):
				continue

			with open(node_obj.dir + os.sep + file_name, "r") as log_file:
				try:
					for each_line in log_file:
						each_line = each_line.rstrip("\n")

						if re.search("check-time' returned non-zero exit status", each_line) is not None:
							node_obj.check_time_fail_count += 1

							if node_obj not in check_time_error_node_objs:
								check_time_error_node_objs.append(node_obj)

				except UnicodeDecodeError:
					continue

	# Print the node table
	if not len(check_time_error_node_objs) == 0:
		node_table = pandas.DataFrame(data = {
				"IP": [o.ip for o in check_time_error_node_objs],
				"Type": [o.type for o in check_time_error_node_objs],
				"check-time Fails": [o.check_time_fail_count for o in check_time_error_node_objs],
			}
		)

		node_table.sort_values("check-time Fails", inplace=True, ascending=False)

		node_table.reset_index(inplace=True, drop=True)

		node_table.index += 1

		print(node_table)



def kmem_presence(node_objs):
	"""Check for the kmem bug on agent nodes
	"""
	print("Checking for kmem bug")

	kmem_error_node_objs = list()

	for node_obj in node_objs:
		if node_obj.type == "master":
			continue

		if os.path.exists(node_obj.dir + os.sep + "dmesg_-T-0.output"):
			dmesg_file = node_obj.dir + os.sep + "dmesg_-T-0.output"

		elif os.path.exists(node_obj.dir + os.sep + "dmesg_-T.output"):
			dmesg_file = node_obj.dir + os.sep + "dmesg_-T.output"

		elif os.path.exists(node_obj.dir + os.sep + "dmesg-0.output"):
			dmesg_file = node_obj.dir + os.sep + "dmesg-0.output"

		elif os.path.exists(node_obj.dir + os.sep + "dmesg_t.log"):
			dmesg_file = node_obj.dir + os.sep + "dmesg_t.log"

		else:
			print("Unable to search for kmem bug, no dmesg file found")

			return

		with open(dmesg_file, "r") as dmesg_file_handle:
			for each_line in dmesg_file_handle:
				each_line = each_line.rstrip("\n")

				if re.search("SLUB: Unable to allocate memory on node -1", each_line) is not None:
					node_obj.kmem_slub_error_count += 1

					if node_obj not in kmem_error_node_objs:
						kmem_error_node_objs.append(node_obj)


	# Print the node table
	if not len(kmem_error_node_objs) == 0:
		node_table = pandas.DataFrame(data = {
				"IP": [o.ip for o in kmem_error_node_objs],
				"Type": [o.type for o in kmem_error_node_objs],
				"kmem SLUB Errors": [o.kmem_slub_error_count for o in kmem_error_node_objs],
			}
		)

		node_table.sort_values("kmem SLUB Errors", inplace=True, ascending=False)

		node_table.reset_index(inplace=True, drop=True)

		node_table.index += 1

		print(node_table)



def zk_fsync(node_objs):
	"""Check for long fsync times in ZooKeeper.
	"""
	print("Checking for slow fsync in ZooKeeper")

	zk_fsync_node_objs = list()

	for node_obj in node_objs:
		if not node_obj.type == "master":
			continue

		if os.path.exists(node_obj.dir + os.sep + "dcos-exhibitor.service"):
			exhibitor_log = node_obj.dir + os.sep + "dcos-exhibitor.service"

		elif os.path.exists(node_obj.dir + os.sep + "dcos-exhibitor.service.log"):
			exhibitor_log = node_obj.dir + os.sep + "dcos-exhibitor.service.log"

		with open(exhibitor_log, "r") as zk_file_handle:
			for each_line in zk_file_handle:
				each_line = each_line.rstrip("\n")

				match = re.search("fsync-ing the write ahead log in SyncThread:\d+ took\s(\d+)ms", each_line)

				if match is not None:
					node_obj.zk_fsync_warning_count += 1

					#FIXME: Get the actual value
					node_obj.add_zk_fsync(match.group(1))

					if node_obj not in zk_fsync_node_objs:
						zk_fsync_node_objs.append(node_obj)


	# Print the node table
	if not len(zk_fsync_node_objs) == 0:
		node_table = pandas.DataFrame(data = {
				"IP": [o.ip for o in zk_fsync_node_objs],
				"ZK fsync Warnings": [o.zk_fsync_warning_count for o in zk_fsync_node_objs],
				"ZK Longest fsyncs (ms)": [o.get_longest_zk_fsyncs() for o in zk_fsync_node_objs],
			}
		)

		node_table.sort_values("ZK fsync Warnings", inplace=True, ascending=False)

		node_table.reset_index(inplace=True, drop=True)

		node_table.index += 1

		print(node_table)



def zk_diskspace(node_objs):
	"""Check for disk space errors in ZooKeeper.
	"""
	print("Checking for disk space errors in ZooKeeper")

	zk_diskspace_node_objs = list()

	for node_obj in node_objs:
		if not node_obj.type == "master":
			continue

		if os.path.exists(node_obj.dir + os.sep + "dcos-exhibitor.service"):
			exhibitor_log = node_obj.dir + os.sep + "dcos-exhibitor.service"

		elif os.path.exists(node_obj.dir + os.sep + "dcos-exhibitor.service.log"):
			exhibitor_log = node_obj.dir + os.sep + "dcos-exhibitor.service.log"

		with open(exhibitor_log, "r") as zk_file_handle:
			for each_line in zk_file_handle:
				each_line = each_line.rstrip("\n")

				if re.search("No space left on device", each_line) is not None:
					node_obj.zk_diskspace_error_found = True

					zk_diskspace_node_objs.append(node_obj)

					break


	# Print the node table
	if not len(zk_diskspace_node_objs) == 0:
		node_table = pandas.DataFrame(data = {
				"IP": [o.ip for o in zk_diskspace_node_objs],
				"ZK Disk Space Error": [o.zk_diskspace_error_found for o in zk_diskspace_node_objs],
			}
		)

		node_table.sort_values("ZK Disk Space Error", inplace=True, ascending=False)

		node_table.reset_index(inplace=True, drop=True)

		node_table.index += 1

		print(node_table)



def oom_presence(node_objs):
	"""Check for out-of-memory events.
	"""
	print("Checking for ooms")

	oom_node_objs = list()

	for node_obj in node_objs:
		if os.path.exists(node_obj.dir + os.sep + "dmesg_-T-0.output"):
			dmesg_file = node_obj.dir + os.sep + "dmesg_-T-0.output"

		elif os.path.exists(node_obj.dir + os.sep + "dmesg_-T.output"):
			dmesg_file = node_obj.dir + os.sep + "dmesg_-T.output"

		elif os.path.exists(node_obj.dir + os.sep + "dmesg-0.output"):
			dmesg_file = node_obj.dir + os.sep + "dmesg-0.output"

		elif os.path.exists(node_obj.dir + os.sep + "dmesg_t.log"):
			dmesg_file = node_obj.dir + os.sep + "dmesg_t.log"

		else:
			print("Unable to search for ooms, no dmesg file found")

			return

		with open(dmesg_file, "r") as dmesg_file_handle:
			for each_line in dmesg_file_handle:
				each_line = each_line.rstrip("\n")

				# FIXME: Get the killed process not the one that invoked oom-killer
				match = re.search("Killed process \d+ \(([^\s]+)\)", each_line)

				if match is not None:
					node_obj.oom_invoked_count += 1

					node_obj.add_oom_proc(match.group(1))

					if node_obj not in oom_node_objs:
						oom_node_objs.append(node_obj)

					
	# Print the node table
	if not len(oom_node_objs) == 0:
		node_table = pandas.DataFrame(data = {
				"IP": [o.ip for o in oom_node_objs],
				"Type": [o.type for o in oom_node_objs],
				"oom-killer Invoked": [o.oom_invoked_count for o in oom_node_objs],
				"Top 5 oom Processes": [o.get_top_oom_procs() for o in oom_node_objs],
			}
		)

		node_table.sort_values("oom-killer Invoked", inplace=True, ascending=False)

		node_table.reset_index(inplace=True, drop=True)

		node_table.index += 1

		print(node_table)



def crdb_ranges(node_objs):
	"""Check the health of CockroachDB"
	"""
	print("Checking CRBD")

	underrep_ranges_node_objs = list()

	for node_obj in node_objs:
		if not node_obj.type == "master":
			continue

		if os.path.exists(node_obj.dir + os.sep + "dcos-checks-poststart.service"):
			poststart_log = node_obj.dir + os.sep + "dcos-checks-poststart.service"

		elif os.path.exists(node_obj.dir + os.sep + "dcos-checks-poststart.service.log"):
			poststart_log = node_obj.dir + os.sep + "dcos-checks-poststart.service.log"

		else:
			raise Exception("No dcos-checks-poststart.service log found")

		with open(poststart_log, "r") as poststart_file:
			for each_line in poststart_file:
				each_line = each_line.rstrip("\n")
			
				if re.search("CockroachDB has underreplicated ranges", each_line) is not None:
					node_obj.crdb_has_underrep_ranges = True

					underrep_ranges_node_objs.append(node_obj)

					break


	# Print the node table
	if not len(underrep_ranges_node_objs) == 0:
		node_table = pandas.DataFrame(data = {
				"IP": [o.ip for o in underrep_ranges_node_objs],
				"Type": [o.type for o in underrep_ranges_node_objs],
				"CRDB Underreplicated Ranges": [o.crdb_has_underrep_ranges for o in underrep_ranges_node_objs],
			}
		)

		node_table.sort_values("IP", inplace=True, ascending=False)

		node_table.reset_index(inplace=True, drop=True)

		node_table.index += 1

		print(node_table)



def state_size(node_objs):
	"""Check the size of Mesos' state.json and warn if it is large.
	"""

	print("Checking for large state.json")

	for node_obj in node_objs:
		if not node_obj.type == "master":
			continue

		if os.path.exists(node_obj.dir + os.sep + "5050-master_state.json"):
			state_size = os.stat(node_obj.dir + os.sep + "5050-master_state.json").st_size

			if state_size > 5242880:
				print("Warning: Mesos state.json is larger than 5MB (" + str(round(state_size / 1024 / 1024, 2)) + " MB)")

			break

