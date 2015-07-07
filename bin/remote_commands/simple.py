import os
import os.path
import sys
import itertools
import collections
sys.path.append(
		os.path.join(
				os.environ.get( "SPLUNK_HOME", "/opt/splunk/6.1.3" ),
				"etc/apps/framework/contrib/splunk-sdk-python/1.3.0",
		)
)
import execnet
from splunklib.searchcommands import StreamingCommand, ReportingCommand, Configuration

class SimpleRemoteCommand(object):
	code = """
	import sys, os
	if __name__ == '__channelexec__':
		items = []
		for record in channel:
			if not record:
				break
			items.append(record)

		for record in items:
			record['from_remote'] = 1
			channel.send(record)
"""

	# model_file = ""
	# save_model = False # Override

	def __init__(self, *args, **kwargs):
		super(SimpleRemoteCommand, self).__init__(*args, **kwargs)
		mdir, _ = os.path.split(__file__)
		cdir = os.path.normpath(os.path.join(mdir, ".."))
		self.gw = execnet.makegateway("popen//python=/usr/bin/python//chdir=%s" % cdir)

	def remote_exec(self, records, code):
		channel = self.gw.remote_exec(code)

		retval = []
		for record in records:
			channel.send(record)

		channel.send(None)

		channel.setcallback(retval.append)
		channel.waitclose()

		return retval

	def remote_stream(self, records):
		if not type(self).code:
			return
		return self.remote_exec(records, type(self).code)

class SimpleRemoteStreamingCommand(StreamingCommand, SimpleRemoteCommand):

	def __init__(self, *args, **kwargs):
		StreamingCommand.__init__(self, *args, **kwargs)
		SimpleRemoteCommand.__init__(self, *args, **kwargs)

	def stream(self, records):
		for record in self.remote_stream(records):
			yield record

class SimpleRemoteReportingCommand(ReportingCommand, SimpleRemoteCommand):
	reduce_code = """
	import sys, os
	if __name__ == '__channelexec__':
		items = []
		for record in channel:
			if not record:
				break
			items.append(record)

		channel.send({ 'total_remote': len(items) })
"""
	def __init__(self, *args, **kwargs):
		ReportingCommand.__init__(self, *args, **kwargs)
		SimpleRemoteCommand.__init__(self, *args, **kwargs)

	def remote_reduce(self, records):
		if not type(self).reduce_code:
			return

		return self.remote_exec(records, type(self).reduce_code)

	def map(self, records):
		for record in self.remote_stream(records):
			yield record

	def reduce(self, records):
		for record in self.remote_reduce(records):
			if '_fields' in record:
				fields = record.pop('_fields')
				yield collections.OrderedDict(sorted(record.items(),key=lambda t: fields.index(t[0])))
			else:
				yield record


class MultiRemoteReportingCommand(SimpleRemoteReportingCommand):
	default_args = ''
	reduce_code = """
	import sys, os
	if __name__ == '__channelexec__':
		args = None
		items = []
		for record in channel:
			if not record:
				break
			if isinstance(item, basestring):
				args = item
				continue
			items.append(record)

		channel.send({ 'total_remote': len(items) })
"""

	def reduce(self, records):
		args = type(self).default_args

		if self.fieldnames:
			args = [s.lower() for s in self.fieldnames]
			args = u" ".join(args)

		for record in self.remote_exec(itertools.chain([args],records), type(self).reduce_code):
			if 'error' in record:
				self.messages.append('error_message', record['error'])
				return
			if '_fields' in record:
				fields = record.pop('_fields')
				yield collections.OrderedDict(sorted(record.items(),key=lambda t: fields.index(t[0])))
			else:
				yield record

class OptionCommandMixin(object):
	default_args = {}

	def getargs(self):
		args = type(self).default_args or {}

		for attr in dir(self):
			item = getattr(self, attr, None)
			if isinstance(item, file):
				args[attr] = item.name
			else:
				args[attr] = item

		if self.fieldnames:
			args['fieldnames'] = self.fieldnames

		return args

	def clean_generator(self, records):
		try:
			for record in records:
				yield record
		except:
			yield {}


class OptionRemoteStreamingCommand(SimpleRemoteStreamingCommand, OptionCommandMixin):
	default_args = {}

	def __dir__(self):
		raise "Please implement __dir__ to get the list of options"


	def stream(self, records):
		args = self.getargs()

		for record in self.remote_exec(itertools.chain([args],self.clean_generator(records)), type(self).code):
			if 'error' in record:
				self.messages.append('error_message', record['error'])
				return
			yield record


class OptionRemoteReportingCommand(SimpleRemoteReportingCommand, OptionCommandMixin):
	default_args = {}
	reduce_code = """
	import sys, os
	if __name__ == '__channelexec__':
		args = None
		items = []

		for record in channel:
			if not record:
				break
			if not args:
				args = item
				continue
			items.append(record)

		channel.send({ 'total_remote': len(items) })
"""
	
	def __dir__(self):
		raise "Please implement __dir__ to get the list of options"

	def reduce(self, records):
		args = self.getargs()

		for record in self.remote_exec(itertools.chain([args],self.clean_generator(records)), type(self).reduce_code):
			if 'error' in record:
				self.messages.append('error_message', record['error'])
				return
			if '_fields' in record:
				fields = record.pop('_fields')
				yield collections.OrderedDict(sorted(record.items(),key=lambda t: fields.index(t[0])))
			else:
				yield record



