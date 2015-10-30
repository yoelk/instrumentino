from kivy.uix.widget import Widget
from kivy.config import ConfigParser
from kivy.properties import ObjectProperty
from instrumentino.users import User

class Instrument(Widget):

    app = ObjectProperty(None)

    def __init__(self, **kwargs):
        # Reqired: app
        super(Instrument, self).__init__(**kwargs)

    def GetConfig(self,instrumentDir,instrumentName):

        # Get manifest
        instrumentCfg = ConfigParser()
        instrumentCfg.read(instrumentDir+'/'+instrumentName+'/config.ini')
        
        return instrumentCfg

    def Load(self,instrumentName): # TO DO
        user = User(app=self.app)
        instrumentDir = user.GetConfigValue('instruments_dir')
        print 'TO DO -> Loading instrument: '+instrumentName+' from Instruments dir: '+instrumentDir
        
        pass
