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
from remote_commands import OptionRemoteStreamingCommand

class FloatValidator(validators.Integer):
	def __init__(self, **kwargs):
		super(FloatValidator, self).__init__(**kwargs)

	def __call__(self, value):
		if value is not None:
			value = float(value)
			self.check_range(value)
		return value

@Configuration(clear_required_fields=True, run_in_preview=False)
class Outliers(OptionRemoteStreamingCommand):
	threshold = Option(require=False, default=0.01, validate=FloatValidator(minimum=0,maximum=1))

	# One-Class SVM arguments
	kernel = Option(require=False, default='rbf')
	degree = Option(require=False, default=3, validate=validators.Integer(minimum=1))
	gamma = Option(require=False, default=0.1, validate=FloatValidator(minimum=0, maximum=1))
	coef0 = Option(require=False, default=0.0, validate=FloatValidator())

	# Covariance Estimator arguments
	support_fraction = Option(require=False, validate=FloatValidator(minimum=0, maximum=1))
	showmah = Option(require=False, default=False, validate=validators.Boolean())

	classifier = Option(require=False, default='one_class_svm')

	code = """
import os, sys, numbers, math
import numpy as np
import scipy.sparse as sp
from scipy import stats

from sklearn import svm
from sklearn.covariance import EllipticEnvelope
from sklearn.feature_extraction.text import HashingVectorizer

if __name__ == '__channelexec__':
	args = channel.receive()

	fraction = 1 - args['threshold']
	fields = args.get('fieldnames') or ['_raw']
	by_fields = None
	try:
		by_index = fields.index("by")
		by_fields = fields[(by_index+1):]
		fields = fields[:by_index]
	except:
		pass
	classifier = args['classifier']

	svm_args = {
		'nu': 0.95 * fraction + 0.05,
		'kernel': args['kernel'],
		'degree': args['degree'],
		'gamma': args['gamma'],
		'coef0': args['coef0']
	}

	rc_args = {
		'contamination': args['threshold'],
		'support_fraction': args['support_fraction']
	}

	classifiers = {
		'one_class_svm': svm.OneClassSVM(**svm_args),
		'covariance_estimator': EllipticEnvelope(**rc_args)
	}

	records = []
	for record in channel:
		if not record:
			break
		records.append(record)

	if records:
		vectorizer = HashingVectorizer(ngram_range=(1,3), n_features=int(math.sqrt(len(records))))
		X = sp.lil_matrix((len(records),vectorizer.n_features))

		for i, record in enumerate(records):
			nums = []
			strs = []
			for field in fields:
				if isinstance(record.get(field), numbers.Number):
					nums.append(record[field])
				else:
					strs.append(str(record.get(field) or ""))
			if nums:
				X[i] = np.array(nums, dtype=np.float64)
			elif strs:
				X[i] = vectorizer.transform([" ".join(strs)])

		X = X.toarray()
		y_pred = None
		mah = None

		clf = classifiers.get(classifier)
		if clf:
			try:
				clf.fit(X)
				y = clf.decision_function(X).ravel()
				threshold = stats.scoreatpercentile(y, 100 * fraction)
				y_pred = y > threshold
				if classifier == 'covariance_estimator' and args['showmah']:
					mah = clf.mahalanobis(X)
			except ValueError:
				y_pred = np.zeros((X.shape[0]))

			for i, y in enumerate(y_pred):
				if y:
					record = records[i]
					if mah is not None:
						record['mahalanobis'] = mah[i].item()
					channel.send(record)
		else:
			channel.send({ "error": "Incorrect classifier specified %s" % classifier })
"""

	def __dir__(self):
		return ['threshold','kernel','degree','gamma','coef0','support_fraction','showmah','classifier']

dispatch(Outliers, sys.argv, sys.stdin, sys.stdout, __name__)
