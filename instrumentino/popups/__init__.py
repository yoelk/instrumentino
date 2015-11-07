from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty,ObjectProperty
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from instrumentino.instruments import Instrument
from instrumentino.users import User

from kivy.config import ConfigParser

from os.path import dirname, join
import os
from kivy.app import App

############################
# BEGIN: File Chooser
# http://kivy.org/docs/api-kivy.uix.filechooser.html?highlight=loaddialog
############################
class FileChooserLoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    
class FileChooserSaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

class FileChooser (FloatLayout):
    '''Allows selecting a file name on the filesystem to load or save
    '''
    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self,dir,filter):
        
        content = FileChooserLoadDialog(load=self.load, cancel=self.dismiss_popup)
        content.filechooser_widget.path=dir
        content.filechooser_widget.filters=filter
        
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def show_save(self,dir,filter):
        content = FileChooserSaveDialog(save=self.save, cancel=self.dismiss_popup)
        content.filechooser_widget.path=dir
        content.filechooser_widget.filters=filter
        
        self._popup = Popup(title="Save file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        print "Would have loaded file: " + os.path.join(path, filename[0])
        #with open(os.path.join(path, filename[0])) as stream:
        #    self.text_input.text = stream.read()

        self.dismiss_popup()

    def save(self, path, filename):
        print "Would have saved file: " + os.path.join(path, filename)
        #with open(os.path.join(path, filename), 'w') as stream:
        #    stream.write(self.text_input.text)

        self.dismiss_popup()

############################
# END: File Chooser
############################

class ExitConfirmation(Popup):
    '''Exit confirmation UI
    '''
    pass

class ActivityLog(Popup):
    '''Activity log UI
    '''
    pass

class Help(Popup):
    '''General Help UI
    '''
    pass     

class ProfileLoader(Popup):
    '''UI to allow choosing a user and an instrument combination (a profile) to load.
    '''
    userDir = StringProperty(None)
    app = ObjectProperty(None)

    def __init__(self, **kwargs):
        # Required: app
        super(ProfileLoader, self).__init__(**kwargs)
        
        # Check if user dir exists
        # Note: If the global user dir is changed in mid-run, the 
        #       current profile may not exist there.
        self.userDir = self.app.config.get('DEFAULT', 'user_dir')
        if(os.path.exists(self.userDir)):
            userCurrent = self.app.config.get('DEFAULT', 'user_current')
            #self.ids.status.text = 'Current profile: ' + userCurrent

            # Load list of exsting users to chose from
            for dirName in os.listdir(self.userDir):

                path = os.path.join(self.userDir, dirName)
                
                if os.path.isdir(path): # Add the user to the selection list
                    self.ids.users.values.append(dirName)
                    if(dirName == userCurrent): # Set as default selection (may not happen!
                        self.ids.users.text = userCurrent
        else:
            print 'ERROR:ProfileLoader User dir: ' + self.userDir + ' does not exist.'
        
        # Load the Instruments for the selected user
        #self.LoadProfile()

    def GetUserInstrumentNames(self):
        '''For selecting instruments. 
           Using the user selected in the UI, Loads list of instrument names
           from the users instruments directory as well as the manifest for the instrument
           selected
        '''
        userName = self.ids.users.text
        user = User(app=self.app)

        # Load the instrument list for the profile
        self.ids.instruments.values = []

        lastInstrument = user.TestConfigValue(userName,'last_instrument_used')
        instrumentsDir = user.TestConfigValue(userName,'instruments_dir')

        # Load list of exsting instruments to chose from
        for dirName in os.listdir(instrumentsDir):
            path = os.path.join(instrumentsDir, dirName)
            
            if os.path.isdir(path): # Add the instrument to the selection list
                self.ids.instruments.values.append(dirName)
                if(dirName == lastInstrument): # Set as default selection (may not happen!
                    self.ids.instruments.text = lastInstrument
                    # Get the instrument manifest for the selected instrument
                    self.GetInstrumentManifest(lastInstrument)

    def LoadProfile(self):
        '''Loads a user and instrument from data chosen in the UI
        '''
        userName = self.ids.users.text
        user = User(app=self.app)
        user.LoadProfile(userName)
        
        instrumentName = self.ids.instruments.text
        instrument = Instrument(app=self.app)
        instrument.Load(instrumentName)

        #self.ids.status.text = 'Loaded profile: ' + userName

    def GetInstrumentManifest(self,InstrumentName):
        '''Loads the instrument manifest into the UI using 
           the instrument name selected in the UI
        '''
        user = User(app=self.app)
        instrumentName = self.ids.instruments.text
        instrumentDir = user.GetConfigValue('instruments_dir')
        instrument = Instrument()
        cfg = instrument.GetConfig(instrumentDir,instrumentName)
        
        manifest = ''
        for option in cfg.options('INSTRUMENT'):
            val = cfg.get('INSTRUMENT', option)
            manifest = manifest+option+': '+val+'\n'
        self.ids.status.text=manifest

    def Close(self):
        '''Closes the ProfileLoader UI
        '''
        self.dismiss()
