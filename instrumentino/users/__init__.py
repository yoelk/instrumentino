from kivy.uix.widget import Widget
from kivy.config import ConfigParser
from kivy.properties import ObjectProperty

from os.path import dirname, join
import os


class User(Widget):
    app = ObjectProperty(None)

    def __init__(self, **kwargs):
        # Required: app
        super(User, self).__init__(**kwargs)

    def Create(self, userDir, userId, settings):  # TO DO
        # Check if user exists
        # path = os.path.join(userDir, userId)
        # if(os.path.exists(path)):
        #    if os.path.isdir(path):
        #        # Do nothing?
        #        print 'ERROR:User:Create User: ' + userId + ' already exists.'
        #        pass

        # User does not exist. Create basic user files
        # print 'DEBUG:User:Create. User: ' + userId + ' does not exist. Creating.'
        # os.mkdir(os.path.join(userDir, userId))
        pass

    def Delete(userDir, userId):  # TO DO
        pass

    def LoadProfile(self, userName):
        userCurrent = self.app.config.get('DEFAULT', 'user_current')
        userDir = self.app.config.get('DEFAULT', 'user_dir')

        # Get user profile
        profileCfg = ConfigParser()
        profileCfg.read(userDir + '/' + userName + '/user.ini')

        # Load user profile.
        # Set user_current first so profile can access it?
        self.app.config.set('DEFAULT', 'user_current', userName)

        for option in profileCfg.options('USER_PROFILE'):
            val = profileCfg.get('USER_PROFILE', option)
            self.app.config.set('USER_PROFILE', option, val)

    def TestConfigValue(self, userName, option):
        # Get what the config value would be for a user if it WERE loaded.
        # If val = DEFAULT, get the global profile default
        userDir = self.app.config.get('DEFAULT', 'user_dir')

        # Get user profile
        profileCfg = ConfigParser()
        profileCfg.read(userDir + '/' + userName + '/user.ini')

        if (profileCfg.get('USER_PROFILE', option) == 'DEFAULT'):
            return self.app.config.get('USER_PROFILE_DEFAULTS', option)
        else:
            return profileCfg.get('USER_PROFILE', option)

    def GetConfigValue(self, option):
        # Get the option. If val = DEFAULT, get the global profile default
        if (self.app.config.get('USER_PROFILE', option) == 'DEFAULT'):
            return self.app.config.get('USER_PROFILE_DEFAULTS', option)
        else:
            return self.app.config.get('USER_PROFILE', option)
