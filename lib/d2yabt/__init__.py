#!/usr/bin/env python3
"""This file loads the other library files of d2yabt.  It also defines
any classes provided by d2yabt.
"""



import operator
import d2yabt.util
import d2yabt.dcos.bundle
import d2yabt.dcos.check
import d2yabt.service.bundle
import d2yabt.service.check
import d2yabt.konvoy.bundle
import d2yabt.konvoy.check



__version__ = "1.0.4"



class Node:
	"""This class holds information about a DC/OS or Konvoy node.
	"""
	def __init__(self):
		self.ip = ""
		self.type = ""
		self.dir = ""
		self.os = ""
		self.dcos_version = ""
		self.docker_verison = ""
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

