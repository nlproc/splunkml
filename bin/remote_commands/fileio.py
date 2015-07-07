import os, os.path
from splunklib.searchcommands import validators

def get_directory(where='default'):
	mdir, _ = os.path.split(__file__)
	return os.path.join(mdir, "..", "..", where)

def get_path_to_file(filename, where='default', subdir=None):
	mdir, _ = os.path.split(__file__)
	if subdir:
		subdir_path = os.path.join(mdir, "..", "..", where, subdir)
		if not os.path.exists(subdir_path):
			os.mkdir(subdir_path)
		return os.path.join(subdir_path, filename)
	return os.path.join(mdir, "..", "..", where, filename)

class ValidateFile(validators.File):
	where = 'local'

	def __init__(self, mode='ab', buffering=-1, extension=None, subdir=None, nohandle=False):
		super(ValidateFile, self).__init__(mode, buffering)
		self.extension = extension
		self.nohandle = nohandle
		self.subdir = subdir

	def __call__(self, value):
		if isinstance(value, basestring):
			if self.extension and not value.endswith(".%s" % self.extension):
				value = "%s.%s" % (value, self.extension)
			filename = get_path_to_file(value, type(self).where, self.subdir)
			if self.nohandle:
				return filename
			else:
				value = super(ValidateFile, self).__call__(filename)
		return value

	def format(self, value):
		if isinstance(value, basestring):
			if self.extension and not value.endswith(".%s" % self.extension):
				value = "%s.%s" % (value, self.extension)
			return get_path_to_file(value, type(self).where, self.subdir)
		return getattr(value, 'name', str(value))

class ValidateLocalFile(ValidateFile):
	where = 'local'

class ValidateDefaultFile(ValidateFile):
	where = 'default'
