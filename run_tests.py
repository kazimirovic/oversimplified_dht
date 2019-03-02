import doctest
import unittest

from oversimplified_dht import node, node_id

doctest.testmod(node)
doctest.testmod(node_id)

loader = unittest.TestLoader()
tests = loader.discover('.')
testRunner = unittest.TextTestRunner()
testRunner.run(tests)
