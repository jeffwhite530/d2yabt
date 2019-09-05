#!/usr/bin/env python3



import operator
import yabt.util
import yabt.dcos.bundle
import yabt.dcos.check
import yabt.service.bundle
import yabt.konvoy.bundle



class Node:
	"""This class holds information about a DC/OS node.
	"""
	def __init__(self):
		self.ip = ""
		self.type = ""
		self.dir = ""
		self.dcos_version = ""
		self.zk_fsync_warning_count = 0
		self._zk_longest_fsyncs = list()
		self.oom_invoked_count = 0
		self._oom_procs = dict()


	def add_zk_fsync(self, zk_fsync: int):
		"""Add an ZK fsync time entry.
		"""
		self._zk_longest_fsyncs.append(zk_fsync)
		self._zk_longest_fsyncs.sort(reverse=True)
		self._zk_longest_fsyncs = self._zk_longest_fsyncs[:5]


	def get_longest_zk_fsyncs(self):
		"""Returns a list of the top 5 longest ZK fsync times.
		"""
		return self._zk_longest_fsyncs


	def add_oom_proc(self, oom_proc):
		"""Add a process to the list of ones which invoked oom-killer.
		"""
		if oom_proc not in self._oom_procs:
			self._oom_procs[oom_proc] = 1

		else:
			self._oom_procs[oom_proc] += 1


	def get_top_oom_procs(self):
		"""Returns a dict of the top 5 processes which invoked oom-killer.
		"""
		return sorted(self._oom_procs.items(), key=operator.itemgetter(1), reverse=True)[0:5]

