#!env python
import os
import sys
sys.path.append(
		os.path.join(
				os.environ.get( "SPLUNK_HOME", "/opt/splunk/6.1.3" ),
				"etc/apps/framework/contrib/splunk-sdk-python/1.3.0",
		)
)
from collections import Counter, OrderedDict
from math import log
from nltk import tokenize
import execnet
import json
from splunklib.searchcommands import Configuration, Option
from splunklib.searchcommands import dispatch, validators
from remote_commands import OptionRemoteReportingCommand, ValidateLocalFile, ValidateFloat

class ValidateTestSize(validators.Validator):

	def __init__(self, **kwargs):
		super(ValidateTestSize, self).__init__()
		int_args = {
			'minimum': kwargs.get('int_minimum'),
			'maximum': kwargs.get('int_maximum'),
		}
		float_args = {
			'minimum': kwargs.get('float_minimum'),
			'maximum': kwargs.get('float_maximum'),
		}
		self.validate_int = validators.Integer(**int_args)
		self.validate_float = ValidateFloat(**float_args)

	def __call__(self, value):
		import numbers
		if value is not None and not isinstance(value, numbers.Number):
			try:
				test = int(value)
				self.validate_int.check_range(test)
				return test
			except ValueError:
				value = float(value)
				self.validate_float.check_range(value)
		return value

	def format(self, value):
		return str(value)



@Configuration(clear_required_fields=True, requires_preop=False, run_in_preview=False)
class MCTrain(OptionRemoteReportingCommand):
	model = Option(require=True, validate=ValidateLocalFile(extension="pkl",subdir='classifiers',nohandle=True))
	target = Option(require=True, validate=validators.Fieldname())

	reset = Option(require=False, default=False, validate=validators.Boolean())
	textmodel = Option(require=False, default='hashing')
	test_size = Option(require=False, default=0.25, validate=ValidateTestSize(int_minimum=0,float_minimum=0,float_maximum=1))
	_C = Option(require=False, default=1.0, validate=ValidateFloat(minimum=0.0))

	reduce_code = """
import os, sys, itertools, collections, numbers
import numpy as np
import scipy.sparse as sp

from multiclassify import process_records

# Can try one of these 2
from gensim.models import LsiModel, TfidfModel, LdaModel

from sklearn.linear_model import LogisticRegression
# from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.preprocessing import LabelEncoder

from sklearn.cross_validation import train_test_split

from sklearn.externals import joblib

if __name__ == "__channelexec__":
	args = channel.receive()
	fields = args.get('fieldnames') or ['_raw']
	target = args['target']

	records = []
	for record in channel:
		if not record:
			break
		records.append(record)

	def is_number(str):
		try:
			n = float(str)
			return True
		except ValueError:
			return False

	if records:
		records = np.array(records)

		# Try loading existing model
		encoder = None
		est = None
		if not args['reset']:
			try:
				model = joblib.load(args['model'])
				encoder = model['encoder']
				est = model['est']
				est.densify()
			except:
				encoder = None
				est = None


		X, y_labels, textmodel = process_records(records, fields, target, args['textmodel'])

		if not encoder:
			encoder = LabelEncoder()

		y = encoder.fit_transform(y_labels)

		print >> sys.stderr, "CLASSES:", encoder.classes_
		X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=args['test_size'])

		if not est:
			kwargs = {
				'C': args['_C'],
			}
			if len(encoder.classes_) <= 2:
				kwargs['multi_class'] = 'ovr'
			else:
				kwargs['multi_class'] = 'multinomial'
				kwargs['solver'] = 'lbfgs'

			est = LogisticRegression(**kwargs)

		est.fit(X_train, y_train)

		score = est.score(X_test, y_test) if len(y_test) > 0 else None

		# Reduce footprint on disk
		if (est.coef_ == 0).sum() > (est.coef_.size / 2):
			est.sparsify()

		model = {
			'encoder': encoder,
			'est': est,
			'score': score,
			'X': X,
			'y_labels': y_labels,
			'target': args['target'],
			'fields': fields,
		}
		if textmodel:
			model['text'] = args['textmodel']
			textmodel.save(args['model'].replace(".pkl",".%s" % args['textmodel']))
		elif args['textmodel'] == 'hashing':
			model['text'] = args['textmodel']

		joblib.dump(model, args['model'])

		print >> sys.stderr, "END"

		channel.send({ 
			'model': args['model'], 
			'score': score.item() if score else None, 
			'training_size': X_train.shape[0],
			'test_size': X_test.shape[0]
		})

"""

	def __dir__(self):
		return ['reset', 'model', 'textmodel', 'test_size', 'target', '_C']

	@Configuration(clear_required_fields=True)
	def map(self, records):
		try:
			for record in records:
				yield record
		except:
			yield {}


dispatch(MCTrain, sys.argv, sys.stdin, sys.stdout, __name__)
