from .simple import SimpleRemoteStreamingCommand, SimpleRemoteReportingCommand, MultiRemoteReportingCommand, OptionRemoteStreamingCommand, OptionRemoteReportingCommand
from .fileio import get_directory, get_path_to_file, ValidateLocalFile

from splunklib.searchcommands import validators

class ValidateFloat(validators.Integer):
	def __init__(self, **kwargs):
		super(ValidateFloat, self).__init__(**kwargs)

	def __call__(self, value):
		if value is not None:
			value = float(value)
			self.check_range(value)
		return value
