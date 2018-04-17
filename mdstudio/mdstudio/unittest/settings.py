import os
import yaml
from pyfakefs.fake_filesystem_unittest import Patcher


class SettingsTestCase():

    def load_settings(self, cls, settings):
        patcher = Patcher()
        patcher.setUp()
        patcher.fs.makedirs(cls.component_root_path(), exist_ok=True)
        #print(os.path.join(cls.component_root_path(), '.settings.yml'),os.path.isdir(cls.component_root_path()), '@@@@@@@@@@@@@@@@@@')

        with open(os.path.join(cls.component_root_path(), '.settings.yml'), 'w') as f:
           # print(f._filesystem, patcher.fs)
            #print(patcher.fs.open_files, patcher.fs.open_files[f], "@")
            yaml.dump(settings,f)

        return patcher