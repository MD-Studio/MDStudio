# coding=utf-8
# loosely based on https://github.com/mailgun/expiringdict
#
# modified to only define the needed functions

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
from threading import Lock
from collections import OrderedDict

class CacheDict(OrderedDict):
    lock = Lock()

    def __init__(self, max_age_seconds):
        super(CacheDict, self).__init__(self)

        self.max_age = max_age_seconds
        assert max_age_seconds >= 0

    def __getitem__(self, key):
        with self.lock:
            item = OrderedDict.__getitem__(self, key)
            age = time.time() - item[1]
            if age < self.max_age:
                return item[0]
            else:
                del self[key]
                raise KeyError(key)

    def __setitem__(self, key, value, **kwargs):
        with self.lock:
            OrderedDict.__setitem__(self, key, (value, time.time()), **kwargs)

    def __contains__(self, key):
        try:
            with self.lock:
                item = OrderedDict.__getitem__(self, key)
                if (time.time() - item[1]) < self.max_age:
                    return True
                else:
                    del self[key]
        except KeyError:
            pass
        return False
