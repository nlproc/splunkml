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
from remote_commands import OptionRemoteStreamingCommand, ValidateLocalFile

@Configuration(clear_required_fields=False)
class MCPredict(OptionRemoteStreamingCommand):
	model = Option(require=True, validate=ValidateLocalFile(mode='r',extension="pkl",subdir='classifiers',nohandle=True))

	code = """
import os, sys, itertools, collections, numbers
try:
	import cStringIO as StringIO
except:
	import StringIO

import numpy as np
import scipy.sparse as sp

from multiclassify import process_records

from gensim.models import LsiModel, TfidfModel, LdaModel

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

from sklearn.externals import joblib

if __name__ == "__channelexec__":
	args = channel.receive()

	records = []
	for record in channel:
		if not record:
			break
		records.append(record)

	if records:
		records = np.array(records)

		# Try loading existing model
		try:
			model = joblib.load(args['model'])
			encoder = model['encoder']
			est = model['est']
			target = model['target']
			fields = model['fields']
			if model.get('text'):
				if model['text'] == 'lsi':
					textmodel = LsiModel.load(args['model'].replace(".pkl",".%s" % model['text']))
				elif model['text'] == 'tfidf':
					textmodel = TfidfModel.load(args['model'].replace(".pkl",".%s" % model['text']))
				else:
					textmodel = model['text']
		except Exception as e:
			print >> sys.stderr, "ERROR", e
			channel.send({ 'error': "Couldn't find model %s" % args['model']})
		else:
			X, y_labels, textmodel = process_records(records, fields, target, textmodel=textmodel)

			print >> sys.stderr, X.shape
			y = est.predict(X)
			y_labels = encoder.inverse_transform(y)

			for i, record in enumerate(records):
				record['%s_predicted' % target] = y_labels.item(i)
				channel.send(record)

"""

	def __dir__(self):
		return ['model']

dispatch(MCPredict, sys.argv, sys.stdin, sys.stdout, __name__)

