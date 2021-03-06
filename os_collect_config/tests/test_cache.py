# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import fixtures
import os
from oslo.config import cfg
import testtools

from os_collect_config import cache
from os_collect_config import collect


class TestCache(testtools.TestCase):
    def setUp(self):
        super(TestCache, self).setUp()
        cfg.CONF.reset()

    def tearDown(self):
        cfg.CONF.reset()
        super(TestCache, self).tearDown()

    def test_cache(self):
        cache_root = self.useFixture(fixtures.TempDir())
        cache_dir = os.path.join(cache_root.path, 'cache')
        collect.setup_conf()
        cfg.CONF(['--cachedir', cache_dir])

        # Never seen, so changed is expected.
        (changed, path) = cache.store('foo', {'a': 1})
        self.assertTrue(changed)
        self.assertTrue(os.path.exists(cache_dir))
        self.assertTrue(os.path.exists(path))
        orig_path = '%s.orig' % path
        self.assertTrue(os.path.exists(orig_path))
        last_path = '%s.last' % path
        self.assertFalse(os.path.exists(last_path))

        # .orig exists now but not .last so this will shortcut to changed
        (changed, path) = cache.store('foo', {'a': 2})
        self.assertTrue(changed)
        orig_path = '%s.orig' % path
        with open(path) as now:
            with open(orig_path) as then:
                self.assertNotEquals(now.read(), then.read())

        # Saves the current copy as .last
        cache.commit('foo')
        last_path = '%s.last' % path
        self.assertTrue(os.path.exists(last_path))

        # We committed this already, so we should have no changes
        (changed, path) = cache.store('foo', {'a': 2})
        self.assertFalse(changed)

        cache.commit('foo')
        # Fully exercising the line-by-line matching now that a .last exists
        (changed, path) = cache.store('foo', {'a': 3})
        self.assertTrue(changed)
        self.assertTrue(os.path.exists(path))
