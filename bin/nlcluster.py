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

@Configuration(clear_required_fields=True, overrides_timeorder=True)
class NLCluster(OptionRemoteStreamingCommand):
	alg = Option(require=False, default="mean_shift")
	model = Option(require=False, default="lsi")
	# threshold = Option(require=False, default=0.01, validate=FloatValidator(minimum=0,maximum=1))

	code = """

import sys, os, numbers
try:
	import cStringIO as StringIO
except:
	import StringIO

import numpy as np
import scipy.sparse as sp

from gensim.corpora import TextCorpus, Dictionary
from gensim.models import LsiModel, TfidfModel, LdaModel
from gensim.similarities import SparseMatrixSimilarity
from gensim.matutils import corpus2dense

from sklearn import cluster, covariance

if __name__ == "__channelexec__":
	args = channel.receive()

# threshold = args['threshold']
	fields = args.get('fieldnames') or ['_raw']

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

	need_sim = args['alg'] in {'affinity_propagation','spectral'}

	if records:
		records = np.array(records)
		input = None # StringIO.StringIO()
		X = None # sp.lil_matrix((len(records),len(fields)))
		for i, record in enumerate(records):
			nums = []
			strs = []
			for field in fields:
				if isinstance(record.get(field), numbers.Number):
					nums.append(record[field])
				elif is_number(record.get(field) or ""):
					nums.append(record[field])
				else:
					strs.append(str(record.get(field) or "").lower())
			if strs:
				if input is None:
					input = StringIO.StringIO()
				print >> input, " ".join(strs)
			else:
				if X is None:
					X = sp.lil_matrix((len(records),len(fields)))
				X[i] = np.array(nums, dtype=np.float64)

		if input is not None:
			corpus = TextCorpus(input)

			if args['alg'] == 'spectral':
				args['model'] = 'tfidf'

			if args['model'] == 'lsi':
				model = LsiModel(corpus)
			elif args['model'] == 'tfidf':
				model = TfidfModel(corpus)
			## Disable this for now
			#
			# elif args['model'] == 'lda':
			# 	model = LdaModel(corpus)
			#
			##
			else:
				model = None

			# TODO: Persist model?
			if model:
				num_terms = len(model.id2word or getattr(model, 'dfs',[]))
				if need_sim:
					index = SparseMatrixSimilarity(model[corpus], num_terms=num_terms)
					X = index[corpus].astype(np.float64)
				else:
					X = corpus2dense(model[corpus], num_terms)
			else:
				channel.send({ 'error': "Unknown model %s" % args['model']})
		else:
			X = X.toarray()
			if need_sim:
				model = covariance.EmpiricalCovariance()
				model.fit(X)
				X = model.covariance_


		if X is not None:
			if args['alg'] == 'affinity_propagation':
				_, labels = cluster.affinity_propagation(X)
			elif args['alg'] == "mean_shift":
				_, labels = cluster.mean_shift(X)
			elif args['alg'] == 'spectral':
				labels = cluster.spectral_clustering(X)
			elif args['alg'] == 'dbscan':
				_, labels = cluster.dbscan(X)
			else:
				labels = None

			if labels != None:
				n_labels = labels.max()

				clustered = []
				for i in range(n_labels + 1):
					clust = records[labels == i]
					record = clust[0]
					record['cluster_label'] = i + 1
					record['cluster_size'] = len(clust)
					channel.send(record)
			else:
				channel.send({ 'error': "Unknown algorithm %s" % args['alg']})
"""

	def __dir__(self):
		return ['alg', 'model']


dispatch(NLCluster, sys.argv, sys.stdin, sys.stdout, __name__)