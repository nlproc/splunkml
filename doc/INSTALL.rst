.. SplunkML Documentation file

SplunkML Installation
================================================

Intro
------------------------------------------------

Thanks for checking out the SplunkML App (Machine Learning Search Commands for Splunk). This doc will help you get up and running with these machine learning commands. Check this document frequently as we update the commands and dependencies might change.


Install Packages
------------------------------------------------

The SplunkML commands require several Python packages to be installed in the Splunk installation's Python library path. However, these will be compiled using your OS's system Python. Because of the nature of the way Splunk's Python binary is compiled, it is incompatible with many of the numeric packages required, e.g.``numpy``.

System Packages
````````````````````````````````````````````````

First, we'll install some packages in your operating system. For the purposes of these instructions, we'll assume you're using an Ubuntu/Debian installation; however, you can modify them for your specific distribution. You'll need these system packages:

  - **python** (Python 2.7.X recommended, no support for Python 3.X yet)
  - **python-dev** (Python development headers)
  - **python-pip** (Pip Python Package Manager)
  - **python-numpy** (NumPy Python Library)
  - **libblas-dev**
  - **liblapack-dev**
  - **gfortran**

Install them using Apt (or your system's package installer if you're not using Ubuntu or Debian).

.. code-block:: bash

  $ apt-get install python python-dev python-pip python-numpy libblas-dev liblapack-dev gfortran

You'll need to install a "standard" Python installation on your system, as well as the development headers for that Python (to compile native bindings for Python dependencies below). The commands rely on a system Python installed in ``/usr/bin/python`` (More on this later). You will also need `Pip <https://pip.pypa.io/en/latest/index.html>`_, the Python package installer. The other 3 packages are dependencies for the Python packages needed in the next section.

A Note on Python Unicode Support
````````````````````````````````````````````````

In the next step, you'll install dependencies for the commands. These dependencies require a Python installation be compiled with UCS-4 Unicode support. Note that Splunk's Python binary does not have UCS-4 support, hence the need to install a separate Python binary. This is the default used by most modern system Python installations. You can verify this support by running the following in the Python interactive shell.

.. code-block:: python

  >>> import sys
  >>> print sys.maxunicode
  1114111

If the value of ``sys.maxunicode`` is not verified as shown here, you will either need to install a Python package with UCS-4 support, or recompile your Python installation using ``--enable-unicode=ucs4`` when you run ``./configure``.

Python Packages using Pip
````````````````````````````````````````````````

Now, we'll install the Python dependencies needed by the commands. You'll use Pip to install these packages, but you'll need to install these packages in a very specific way. For the commands to see these dependencies, they will need to be installed in the Splunk installation's Python library path; however, these libraries will be compiled using the system Python's headers.

  - **execnet** (`Execnet: Distributed Python Deployment and Communication <http://codespeak.net/execnet/index.html>`_)
  - **scikit-learn** (`scikit-learn: Machine Learning in Python <http://scikit-learn.org/stable/>`_)
  - **gensim** (`gensim: Topic modeling for humans <https://radimrehurek.com/gensim/index.html>`_)
  - **splunk-sdk** (`Splunk SDK for Python <http://dev.splunk.com/python>`_, needed for custom search commands)

Install them using Pip. It's best to install each one separately to track potential errors or exceptions.

.. code-block:: bash

  $ sudo pip install -t /opt/splunk/6.2.2/lib/python2.7/site-packages execnet
  ...
  $ sudo pip install -t /opt/splunk/6.2.2/lib/python2.7/site-packages scikit-learn
  ...
  $ sudo pip install -t /opt/splunk/6.2.2/lib/python2.7/site-packages gensim
  ...
  $ sudo pip install -t /opt/splunk/6.2.2/lib/python2.7/site-packages splunk-sdk


Install App into Splunk
------------------------------------------------

Now you can install the app into Splunk. The easiest way to do this is click the *Download ZIP* button on the GitHub page for SplunkML (`https://github.com/nlproc/splunkml`_). You can then install the app by logging on to SplunkWeb in your Splunk installation (ensure that you have the privilege to install apps), and going to *Apps -> Manage Apps*. 

Click the *Install app from file* button and upload the zip file that you just downloaded in the next page. You will then be prompted to restart splunk. Before doing so, login to the shell of the server you just installed the app. Rename the app directory for the newly installed app as follows:

.. code-block:: bash

  $ sudo su -l splunk
  $ cd $SPLUNK_HOME
  $ cd etc/apps/
  $ mv splunkml-<username-changeset-info> splunkml      # GitHub appends this information to directory when you download ZIP
  $ logout

You may then restart splunk as directed by SplunkWeb. 

Using the Commands
------------------------------------------------

To use the commands in SplunkWeb, you will need to change the current application that you are using to the SplunkML app. Go to *Apps -> Splunk ML Commands* in the top bar of SplunkWeb.

You will then have access to the commands in the resulting Splunk search interface.

A Note about Limits 
------------------------------------------------

By default, Splunk uses a default max limit of 50000 result rows for search results. This means that for certain commands (in particular ``mctrain``), you can only process 50000 events/rows at once. This means that the maximum number of training data items is 50000 for most instances. You can adjust this number by modifying ``limits.conf`` in your Splunk installation. Please note that this can be a dangerous modification that can impact other areas of your Splunk installation, and Splunk notes that adjusting this number greater than 50000 causes instability. If you still would like to process more data, and are aware of the risks, you may do the following to edit ``limits.conf``:

.. code-block:: bash

  $ sudo su -l splunk
  $ cd $SPLUNK_HOME
  $ cd etc/system/local
  $ touch limits.conf           # If this file doesn't already exist
  $ vi limits.conf              # You can substitute another editor command here

Add the following section or edit the file to add the following

.. code-block:: cfg

  [searchresults]
  maxresultrows = <your_value_here>


Check out Command Documentation
------------------------------------------------

Now that you are ready to use the SplunkML Commands, you can check out the command documentation for the commmands below. We'll have more commands listed here as we update, so check back again soon.

  - :ref:`splunkml-mctrain`, :ref:`splunkml-mcpredict`
  - :ref:`splunkml-outliers`
  - :ref:`splunkml-nlcluster`

