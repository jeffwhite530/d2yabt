#!/usr/bin/env python3
"""This module contains all of the checks that yabt uses.
"""



# pylint: disable=line-too-long



import sys
import os
import json
import re
import pandas
import datetime



pandas.options.display.max_colwidth = 200
ansi_red_fg = "\033[31m"
ansi_end_color = "\033[0m"


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
			print("Unable to check DC/OS version on", node_obj.ip + ", no dcos-version.json file found")

			continue

	dcos_versions_set = set(dcos_versions_list)

	# Print the node table
	if not len(dcos_versions_set) == 1:
		print(ansi_red_fg + "ALERT: Non-matching DC/OS versions found" + ansi_end_color)

		node_table = pandas.DataFrame(data={
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

	nodes_with_firewalld = list()

	for node_obj in sorted(node_objs, key=lambda x: x.type):
		if not os.path.exists(node_obj.dir + os.sep + "ps_aux_ww_Z.output"):
			print("Unable to check for running firewall on", node_obj.ip + ", no ps output available")

			continue

		with open(node_obj.dir + os.sep + "ps_aux_ww_Z.output", "r") as ps_file:
			for each_line in ps_file:
				each_line = each_line.rstrip("\n")

				if re.search("firewalld", each_line) is not None:
					nodes_with_firewalld.append(node_obj)

	# Print the node table
	if nodes_with_firewalld:
		print(ansi_red_fg + "ALERT: Agents with firewalld running found" + ansi_end_color)

		node_table = pandas.DataFrame(data={
				"IP": [o.ip for o in nodes_with_firewalld],
				"Type": [o.type for o in nodes_with_firewalld]
			}
		)

		node_table.sort_values("Type", inplace=True)

		node_table.reset_index(inplace=True, drop=True)

		node_table.index += 1

		print(node_table)



def unreachable_agents_mesos_log(node_objs):
	"""Check for agents which are unreachable according to the Mesos master and for agent which are not in the bundle.
	"""
	print("Checking for unreachable agents in the Mesos master log")

	unreachable_nodes = list()

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

				match = re.search(r"(\d+-\d+-\d+).*(\d+:\d+:\d+\.\d+).*Marking agent.*\((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\) unreachable", each_line)

				if match is not None:
					date_string = match.group(1)
					time_string = match.group(2)
					unreachable_ip = match.group(3)

					unreachable_datetime = datetime.datetime.strptime(date_string + " " + time_string, "%Y-%m-%d %H:%M:%S.%f")

					unreachable_nodes.append((unreachable_datetime, unreachable_ip))

	# Print the node table
	if unreachable_nodes:
		print(ansi_red_fg + "ALERT: Unreachable agents found in the Mesos master log" + ansi_end_color)

		unreachable_nodes.sort(key=lambda tup: tup[0])

		node_table = pandas.DataFrame(data={
				"Time": [tup[0] for tup in unreachable_nodes],
				"Agent": [tup[1] for tup in unreachable_nodes],
			}
		)

		node_table.index += 1

		print(node_table)

	# Find agents that are mentioned in the Mesos master log but are not in the bundle
	unreachable_ips = set(tup[1] for tup in unreachable_nodes)

	missing_nodes_from_bundle = list()

	for unreachable_ip in sorted(unreachable_ips):
		if not any(x.ip == unreachable_ip for x in node_objs):
			missing_nodes_from_bundle.append(unreachable_ip)

	# Print the node table
	if missing_nodes_from_bundle:
		print(ansi_red_fg + "ALERT: Agents found in Mesos master log but not in the bundle" + ansi_end_color)

		node_table = pandas.DataFrame(data={
				"Agent": missing_nodes_from_bundle,
			}
		)

		node_table.index += 1

		print(node_table)



def check_time_failures(node_objs):
	"""Check for any failures of DC/OS' check-time utility
	"""
	print("Checking for check-time failures")

	check_time_error_nodes = list()

	for node_obj in node_objs:
		check_time_errors = 0

		for file_name in os.listdir(node_obj.dir):
			if not file_name.endswith(".service"):
				continue

			with open(node_obj.dir + os.sep + file_name, "r") as log_file:
				try:
					for each_line in log_file:
						each_line = each_line.rstrip("\n")

						if re.search(r"check-time' returned non-zero exit status", each_line) is not None:
							check_time_errors += 1

				except UnicodeDecodeError:
					continue

		if not check_time_errors == 0:
			check_time_error_nodes.append((node_obj, check_time_errors))

	# Print the node table
	if check_time_error_nodes:
		print(ansi_red_fg + "ALERT: Found nodes with check-time failures" + ansi_end_color)

		node_table = pandas.DataFrame(data={
				"IP": [tup[0].ip for tup in check_time_error_nodes],
				"Type": [tup[0].type for tup in check_time_error_nodes],
				"check-time Failures": [tup[1] for tup in check_time_error_nodes],
			}
		)

		node_table.sort_values("check-time Failures", inplace=True, ascending=False)

		node_table.reset_index(inplace=True, drop=True)

		node_table.index += 1

		print(node_table)



def kmem_presence(node_objs):
	"""Check for the kmem bug on agent nodes
	"""
	print("Checking for kmem bug")

	kmem_error_nodes = list()

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
			print("Unable to search for kmem bug on", node_obj.ip + ", no dmesg file found")

			return

		kmem_slub_error_count = 0

		with open(dmesg_file, "r") as dmesg_file_handle:
			for each_line in dmesg_file_handle:
				each_line = each_line.rstrip("\n")

				if re.search("SLUB: Unable to allocate memory on node -1", each_line) is not None:
					kmem_slub_error_count += 1

		if not kmem_slub_error_count == 0:
			kmem_error_nodes.append((node_obj, kmem_slub_error_count))

	# Print the node table
	if kmem_error_nodes:
		print(ansi_red_fg + "ALERT: Agents with kmem SLUB errors found" + ansi_end_color)

		node_table = pandas.DataFrame(data={
				"IP": [tup[0].ip for tup in kmem_error_nodes],
				"Type": [tup[0].type for tup in kmem_error_nodes],
				"kmem SLUB Errors": [tup[1] for tup in kmem_error_nodes],
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

				match = re.search(r"fsync-ing the write ahead log in SyncThread:\d+ took\s(\d+)ms", each_line)

				if match is not None:
					node_obj.zk_fsync_warning_count += 1

					node_obj.add_zk_fsync(match.group(1))

					if node_obj not in zk_fsync_node_objs:
						zk_fsync_node_objs.append(node_obj)

	# Print the node table
	if zk_fsync_node_objs:
		print(ansi_red_fg + "ALERT: ZooKeeper slow fsync found" + ansi_end_color)

		node_table = pandas.DataFrame(data={
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

	zk_diskspace_nodes = list()

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
					zk_diskspace_nodes.append(node_obj.ip)

					break

	# Print the node table
	if zk_diskspace_nodes:
		print(ansi_red_fg + "ALERT: ZooKeeper disk space error found" + ansi_end_color)

		node_table = pandas.DataFrame(data={
				"IP": zk_diskspace_nodes,
			}
		)

		node_table.sort_values("IP", inplace=True, ascending=False)

		node_table.reset_index(inplace=True, drop=True)

		node_table.index += 1

		print(node_table)



def zk_connection_exception(node_objs):
	"""Check for connection exceptions in ZooKeeper.
	"""
	print("Checking for connection exceptions in ZooKeeper")

	zk_connection_exceptions = dict()

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

				match = re.search(r"Unexpected exception, tries=3, connecting to /(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):2888", each_line)

				if match is not None:
					exception_connection = node_obj.ip + " --> " + match.group(1)

					try:
						zk_connection_exceptions[exception_connection] += 1

					except KeyError:
						zk_connection_exceptions[exception_connection] = 1

	# Print the node table
	if zk_connection_exceptions:
		print(ansi_red_fg + "ALERT: ZooKeeper connection exceptions found" + ansi_end_color)

		node_table = pandas.DataFrame(data={
				"Connection": list(zk_connection_exceptions.keys()),
				"Count": [zk_connection_exceptions[connection] for connection in zk_connection_exceptions.keys()]
			}
		)

		node_table.sort_values("Count", inplace=True, ascending=False)

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
			print("Unable to search for ooms on", node_obj.ip + ", no dmesg file found")

			return

		with open(dmesg_file, "r") as dmesg_file_handle:
			for each_line in dmesg_file_handle:
				each_line = each_line.rstrip("\n")

				match = re.search(r"Killed process \d+ \(([^\s]+)\)", each_line)

				if match is not None:
					node_obj.oom_invoked_count += 1

					node_obj.add_oom_proc(match.group(1))

					if node_obj not in oom_node_objs:
						oom_node_objs.append(node_obj)

	# Print the node table
	if oom_node_objs:
		print(ansi_red_fg + "ALERT: Instances of oom-killer found" + ansi_end_color)

		node_table = pandas.DataFrame(data={
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



def crdb_underrep_ranges(node_objs):
	"""Check for underreplicated ranges in CRDB"
	"""
	print("Checking for underreplicated ranges in CRBD")

	underrep_ranges_nodes = list()

	for node_obj in node_objs:
		if not node_obj.type == "master":
			continue

		if os.path.exists(node_obj.dir + os.sep + "dcos-checks-poststart.service"):
			poststart_log = node_obj.dir + os.sep + "dcos-checks-poststart.service"

		elif os.path.exists(node_obj.dir + os.sep + "dcos-checks-poststart.service.log"):
			poststart_log = node_obj.dir + os.sep + "dcos-checks-poststart.service.log"

		else:
			print("Unable to check for underreplicated ranges in CRDB on", node_obj.ip + ", no dcos-checks-poststart.service log found")

			continue

		with open(poststart_log, "r") as poststart_file:
			for each_line in poststart_file:
				each_line = each_line.rstrip("\n")
			
				if re.search("CockroachDB has underreplicated ranges", each_line) is not None:
					underrep_ranges_nodes.append(node_obj.ip)

					break

	# Print the node table
	if underrep_ranges_nodes:
		print(ansi_red_fg + "ALERT: Nodes with under-replicated ranges in CRDB found" + ansi_end_color)

		node_table = pandas.DataFrame(data={
				"IP": underrep_ranges_nodes,
			}
		)

		node_table.sort_values("IP", inplace=True, ascending=False)

		node_table.reset_index(inplace=True, drop=True)

		node_table.index += 1

		print(node_table)



def crdb_monotonicity_error(node_objs):
	"""Check for time sync errors in CRDB
	"""

	print("Checking for time sync errors in CRDB")


	crdb_timesync_nodes = list()

	for node_obj in node_objs:
		if not node_obj.type == "master":
			continue

		if os.path.exists(node_obj.dir + os.sep + "dcos-cockroach.service"):
			crdb_log = node_obj.dir + os.sep + "dcos-cockroach.service"

		elif os.path.exists(node_obj.dir + os.sep + "dcos-cockroach.service.log"):
			crdb_log = node_obj.dir + os.sep + "dcos-cockroach.service.log"

		else:
			print("Unable to check for time sync errors in CRDB on", node_obj.ip + ", no dcos-cockroach.service log found")

			continue

		error_count = 0

		with open(crdb_log, "r") as crdb_log_handle:
			for each_line in crdb_log_handle:
				each_line = each_line.rstrip("\n")

				if re.search("to ensure monotonicity", each_line) is not None:
					error_count += 1

		if not error_count == 0:
			crdb_timesync_nodes.append((node_obj, error_count))

	# Print the node table
	if crdb_timesync_nodes:
		print(ansi_red_fg + "ALERT: Nodes with time sync errors in CRDB found" + ansi_end_color)

		node_table = pandas.DataFrame(data={
				"IP": [tup[0].ip for tup in crdb_timesync_nodes],
				"Errors": [tup[1] for tup in crdb_timesync_nodes],
			}
		)

		node_table.sort_values("Errors", inplace=True, ascending=False)

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
			state_size_bytes = os.stat(node_obj.dir + os.sep + "5050-master_state.json").st_size

			if state_size_bytes > 5242880:
				print(ansi_red_fg + "ALERT: Mesos state.json is larger than 5MB (" + str(round(state_size_bytes / 1024 / 1024, 2)) + " MB)" + ansi_end_color)

			break



def mesos_leader_changes(node_objs):
	"""Search for Mesos leader changes.
	"""

	print("Checking for Mesos leader changes")

	leader_changes = list()

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

				match = re.search(r"(\d+-\d+-\d+) (\d+:\d+:\d+\.\d+) .* A new leading master \(UPID=master@(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):5050\) is detected", each_line)

				if match is not None:
					date_string = match.group(1)
					time_string = match.group(2)
					leader_ip = match.group(3)

					change_datetime = datetime.datetime.strptime(date_string + " " + time_string, "%Y-%m-%d %H:%M:%S.%f")

					leader_changes.append((change_datetime, leader_ip))

	# Print the node table
	if leader_changes:
		print(ansi_red_fg + "ALERT: Mesos leader changes found" + ansi_end_color)

		leader_changes.sort(key=lambda tup: tup[0])

		node_table = pandas.DataFrame(data={
				"Time": [tup[0] for tup in leader_changes],
				"New Leader": [tup[1] for tup in leader_changes],
			}
		)

		node_table.index += 1

		print(node_table)



def zk_leader_changes(node_objs):
	"""Search for ZooKeeper leader changes.
	"""

	print("Checking for ZooKeeper leader changes")

	leader_changes = list()

	for node_obj in node_objs:
		if not node_obj.type == "master":
			continue

		if os.path.exists(node_obj.dir + os.sep + "dcos-exhibitor.service"):
			exhibitor_log = node_obj.dir + os.sep + "dcos-exhibitor.service"

		elif os.path.exists(node_obj.dir + os.sep + "dcos-exhibitor.service.log"):
			exhibitor_log = node_obj.dir + os.sep + "dcos-exhibitor.service.log"

		with open(exhibitor_log, "r") as exhibitor_log_handle:
			for each_line in exhibitor_log_handle:
				each_line = each_line.rstrip("\n")

				match = re.search(r"(\d+-\d+-\d+) (\d+:\d+:\d+\.\d+) .* LEADING$", each_line)

				if match is not None:
					date_string = match.group(1)
					time_string = match.group(2)

					change_datetime = datetime.datetime.strptime(date_string + " " + time_string, "%Y-%m-%d %H:%M:%S.%f")

					leader_changes.append((change_datetime, node_obj.ip))

	# Print the node table
	if leader_changes:
		print(ansi_red_fg + "ALERT: ZooKeeper leader changes found" + ansi_end_color)

		leader_changes.sort(key=lambda tup: tup[0])

		node_table = pandas.DataFrame(data={
				"Time": [tup[0] for tup in leader_changes],
				"New Leader": [tup[1] for tup in leader_changes],
			}
		)

		node_table.index += 1

		print(node_table)



def marathon_leader_changes(node_objs):
	"""Search for Marathon leader changes.
	"""

	print("Checking for Marathon leader changes")

	leader_changes = list()

	for node_obj in node_objs:
		if not node_obj.type == "master":
			continue

		if os.path.exists(node_obj.dir + os.sep + "dcos-marathon.service"):
			marathon_log = node_obj.dir + os.sep + "dcos-marathon.service"

		elif os.path.exists(node_obj.dir + os.sep + "dcos-marathon.service.log"):
			marathon_log = node_obj.dir + os.sep + "dcos-marathon.service.log"

		else:
			print("Failed to find Marathon log on", node_obj.ip, file=sys.stderr)

			continue

		with open(marathon_log, "r") as marathon_log_handle:
			for each_line in marathon_log_handle:
				each_line = each_line.rstrip("\n")

				match = re.search(r"(\d+-\d+-\d+) (\d+:\d+:\d+\.\d+) .* Leader won: (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):8443", each_line)

				if match is not None:
					date_string = match.group(1)
					time_string = match.group(2)
					leader_ip = match.group(3)

					change_datetime = datetime.datetime.strptime(date_string + " " + time_string, "%Y-%m-%d %H:%M:%S.%f")

					leader_changes.append((change_datetime, leader_ip))

	# Print the node table
	if leader_changes:
		print(ansi_red_fg + "ALERT: Marathon leader changes found" + ansi_end_color)

		leader_changes.sort(key=lambda tup: tup[0])

		node_table = pandas.DataFrame(data={
				"Time": [tup[0] for tup in leader_changes],
				"New Leader": [tup[1] for tup in leader_changes],
			}
		)

		node_table.index += 1

		print(node_table)



def unreachable_agents_mesos_state(node_objs):
	"""Check for unreachable agents in Mesos
	"""
	print("Checking for unreachable agents in the Mesos state")

	unreachable_agents = list()

	for node_obj in node_objs:
		if not node_obj.type == "master":
			continue

		if not os.path.exists(node_obj.dir + os.sep + "5050-registrar_1__registry.json"):
			continue

		with open(node_obj.dir + os.sep + "5050-registrar_1__registry.json", "r") as json_file_handle:
			try:
				json_data = json.load(json_file_handle)

			except json.decoder.JSONDecodeError:
				print("Unable to check for unreachable agents, failed to parse 5050-registrar_1__registry.json", file=sys.stderr)

				continue

		if "unreachable" in json_data and "slaves" in json_data["unreachable"]:
			for entry in json_data["unreachable"]["slaves"]:
				slave_id = entry["id"]["value"]

				# Convert nanoseconds since epoch to a datetime object with microsecond accuracy
				epoch_nanoseconds = entry["timestamp"]["nanoseconds"]
				microseconds = int(str(int(epoch_nanoseconds / 1000 % 1000000)).zfill(6))

				datetime_object = datetime.datetime.fromtimestamp(epoch_nanoseconds // 1000000000)
				datetime_object += datetime.timedelta(microseconds=microseconds)

				unreachable_agents.append((datetime_object, slave_id))

		break

	# Print the node table
	if unreachable_agents:
		print(ansi_red_fg + "ALERT: Unreachable agents found in Mesos state" + ansi_end_color)

		unreachable_agents.sort(key=lambda tup: tup[0])

		node_table = pandas.DataFrame(data={
				"Time": [tup[0] for tup in unreachable_agents],
				"Agent": [tup[1] for tup in unreachable_agents],
			}
		)

		node_table.index += 1

		print(node_table)



def inactive_frameworks(node_objs):
	"""Check for and list any inactive frameworks.
	"""

	print("Checking for inactive frameworks")

	inactive_frameworks = list()

	for node_obj in node_objs:
		if not node_obj.type == "master":
			continue

		if not os.path.exists(node_obj.dir + os.sep + "5050-master_state.json"):
			continue

		with open(node_obj.dir + os.sep + "5050-master_state.json", "r") as json_file_handle:
			try:
				json_data = json.load(json_file_handle)

			except json.decoder.JSONDecodeError:
				print("Unable to check for inactive frameworks, failed to parse 5050-master_state.json", file=sys.stderr)

				break

		for framework in json_data["frameworks"]:
			if framework["active"] is False:
				inactive_frameworks.append((framework["name"], framework["id"]))

		break

	# Print the node table
	if inactive_frameworks:
		print(ansi_red_fg + "ALERT: Found inactive frameworks" + ansi_end_color)

		inactive_frameworks.sort(key=lambda tup: tup[0])

		node_table = pandas.DataFrame(data={
				"Name": [tup[0] for tup in inactive_frameworks],
				"ID": [tup[1] for tup in inactive_frameworks],
			}
		)

		node_table.index += 1

		print(node_table)



def missing_dockerd(node_objs):
	"""Check for agents which do not have a running Docker daemon
	"""

	print("Checking for missing Docker daemon on agents")

	agents_missing_dockerd = list()

	for node_obj in node_objs:
		if node_obj.type == "master":
			continue

		if not os.path.exists(node_obj.dir + os.sep + "ps_aux_ww_Z.output"):
			print("Unable to check for missing Docker daemon on", node_obj.ip + ", no ps output available")

			continue

		with open(node_obj.dir + os.sep + "ps_aux_ww_Z.output", "r") as ps_file:
			found_dockerd = False

			for each_line in ps_file:
				if re.search("dockerd", each_line) is not None:
					found_dockerd = True

					break

			if found_dockerd is False:
				agents_missing_dockerd.append(node_obj.ip)

	# Print the node table
	if agents_missing_dockerd:
		print(ansi_red_fg + "ALERT: Found agents with Docker daemon not running" + ansi_end_color)

		node_table = pandas.DataFrame(data={
				"IP": agents_missing_dockerd,
			}
		)

		node_table.sort_values("IP", inplace=True)

		node_table.reset_index(inplace=True, drop=True)

		node_table.index += 1

		print(node_table)

