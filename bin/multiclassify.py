import sys, os, itertools

try:
	import cStringIO as StringIO
except:
	import StringIO

import numpy as np
import scipy.sparse as sp

from gensim.corpora import TextCorpus
from gensim.models import LsiModel, TfidfModel, LdaModel
from gensim.matutils import corpus2csc

from sklearn.feature_extraction import FeatureHasher
from sklearn.feature_extraction.text import CountVectorizer

from sklearn.decomposition import PCA

def is_number(str):
	try:
		n = float(str)
		return True
	except (ValueError, TypeError):
		return False

def process_records(records, fields, target, textmodel=None):
	tokenize = CountVectorizer().build_analyzer()

	input = None
	X = None
	y_labels = []

	for i, record in enumerate(records):
		nums = []
		strs = []
		y_labels.append(record.get(target))

		for field in fields:
			if is_number(record.get(field)):
				nums.append(record[field])
			else:
				strs.append(str(record.get(field) or "").lower())
		if strs:
			if input is None:
				input = StringIO.StringIO()
			print >> input, " ".join(tokenize(" ".join(strs)))
		if nums:
			if X is None:
				X = sp.lil_matrix((len(records),len(nums)))
			X[i] = np.array(nums, dtype=np.float64)

	if input is not None:
		if X is not None:
			X_2 = X.tocsr()
		else:
			X_2 = None

		if isinstance(textmodel,basestring):
			if textmodel == 'lsi':
				corpus = TextCorpus(input)
				textmodel = LsiModel(corpus, chunksize=1000)
			elif textmodel == 'tfidf':
				corpus = TextCorpus(input)
				textmodel = TfidfModel(corpus)
			elif textmodel == 'hashing':
				textmodel = None
				hasher = FeatureHasher(n_features=2 ** 18, input_type="string")
				input.seek(0)
				X = hasher.transform(tokenize(line.strip()) for line in input)
		if textmodel:
			num_terms = len(textmodel.id2word or getattr(textmodel, 'dfs',[]))
			X = corpus2csc(textmodel[corpus], num_terms).transpose()

		if X_2 is not None:
			# print >> sys.stderr, "X SHAPE:", X.shape
			# print >> sys.stderr, "X_2 SHAPE:", X_2.shape
			X = sp.hstack([X, X_2], format='csr')

	elif X is not None:
		textmodel = None
		X = X.tocsr()

	print >> sys.stderr, "X SHAPE:", X.shape

	return X, y_labels, textmodel


