
Splunk Machine Learning Tools - SplunkML
================================================

SplunkML is a set of search commands for the Splunk Query Language that allows users to train and use machine learning methods on their Splunk data. Included are a binary/multiclass classifier as well as a clustering and outlier detection commands. These commands utilize Machine Learning and Natural Language Processing algorithms from `Scikit-learn <http://scikit-learn.org>`_ and `Gensim <https://radimrehurek.com/gensim/index.html>`_. Please note that this is currently an alpha release; it's not ready for production use at this time. We look forward to your testing and feedback as we further develop these commands.


License
------------------------------------------------

SplunkML is licensed under the Apache License 2.0. Details can be found in the `<LICENSE>`_ file.


Support
------------------------------------------------

This software is released as-is. NLProc provides no warranty and no support on this software. If you have any issues with the software, please feel free to post an Issue on our `Issues <issues>`_ page.

Contributing
------------------------------------------------

We welcome contributions to this project. If you are interested in contributing, please send us an `email <info@nlproc.com>`_.


Introduction
------------------------------------------------

Welcome to SplunkML. Our goal is to provide the best possible Machine Learning tools for `Splunk <http://www.splunk.com>`. Currently we are working on the following Machine Learning tools:

* Binary/multiclass classification, using logistic regression for binary classification models, and multinomial logistic regression for multiclass classification models.
* Outlier detection, using 2 different algorithms (One Class SVM and Robust Covariance Estimation)
* Clustering, using multiple algorithms and multiple linguistic models


Installation
------------------------------------------------

Please see `INSTALL in the doc directory <doc/INSTALL.rst>`_.


Command Documentation
------------------------------------------------

For reference documentation for the search commands, check them out here:

* `mctrain <doc/mctrain.rst>`_, `mcpredict <doc/mcpredict.rst>`_ (Classifier)
* `outliers <doc/outliers.rst>`_ (Outlier detection)
* `nlcluster <doc/nlcluster.rst>`_ (Clustering)

