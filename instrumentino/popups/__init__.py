from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, ObjectProperty, OptionProperty, NumericProperty
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

from instrumentino.instruments import Instrument
from instrumentino.users import User

from kivy.config import ConfigParser

from os.path import dirname, join
import os
from os.path import sep, expanduser, isdir, dirname
from kivy.app import App
from instrumentino.cfg import check_for_necessary_attributes
from kivy.uix.filechooser import FileChooserListView
from kivy.event import EventDispatcher
from kivy.garden.filebrowser import FileBrowser
import ntpath
from pip._vendor.requests.api import head
from kivy.uix.label import Label

class FileDialogPopup(Popup):
    '''A dialog for loading/saving files in a popup. To open, call the open()
    method.
    '''
    
    file_operation =  OptionProperty('load', options=['load', 'save'])
    '''The allowed file operations for this popup
    '''
    
    action_button_text = StringProperty()
    '''The string to be shown on action button
    '''
    
    on_file_choice_callback = ObjectProperty()
    '''Call this function when a file was chosen. The callback is called with
    a string arguments:
    - filepath: full path to the chosen file
    '''
    
    chosen_filepath = StringProperty()
    '''The filepath chosen by the user
    '''
    
    def __init__(self, **kwargs):
        # Act according to the desired file operation
        check_for_necessary_attributes(self, ['file_operation', 'on_file_choice_callback'], kwargs)
        
        # Set strings according to the file operation
        if self.file_operation == 'load':
            self.title = 'Load file'
            self.action_button_text = 'Load'
        elif self.file_operation == 'save':
            self.title = 'Save file'
            self.action_button_text = 'Save'
        
        # Init the file browser
        if os.name == 'nt':
            user_path = dirname(expanduser('~')) + sep + 'Documents'
        else:
            user_path = expanduser('~') + sep + 'Documents'
        browser = FileBrowser(select_string=self.action_button_text,
                              favorites=[(user_path, 'Documents')])
        browser.bind(on_success=self.on_file_choice,
                     on_canceled=self.cancel)

        # Add the browser to the content        
        kwargs['content'] = browser
        
        super(FileDialogPopup, self).__init__(**kwargs)

    def on_file_choice(self, instance):
        '''A file was chosen by the user. Act upon it.
        '''
        # extract file's basename
        head, tail = ntpath.split(instance.filename)
        basename = tail or ntpath.basename(head)
        self.chosen_filepath = os.path.join(instance.path, basename)

        # Check for file overwrite
        if self.file_operation == 'save' and ntpath.exists(self.chosen_filepath):
            ConfirmationPopup(question_text='Overwrite {}?'.format(basename), on_user_choice_callback=self.confirm_overwrite).open()
            return
        
        self.on_file_choice_callback(self.chosen_filepath)
        self.dismiss()
    
    def confirm_overwrite(self, user_agreed):
        '''Act upon the user's agreement to overwrite a file
        '''
        if user_agreed:
            self.on_file_choice_callback(self.chosen_filepath)
            self.dismiss()
        
    def cancel(self, instance):
        '''Cancel this dialog
        '''
        self.dismiss()
    
class LoadFileDialogPopup(FileDialogPopup):
    '''A dialog for file loading
    '''
    
    def __init__(self, **kwargs):
        kwargs['file_operation'] = 'load'
        super(LoadFileDialogPopup, self).__init__(**kwargs)
        
class SaveFileDialogPopup(FileDialogPopup):
    '''A dialog for file saving
    '''
    
    def __init__(self, **kwargs):
        kwargs['file_operation'] = 'save'
        super(SaveFileDialogPopup, self).__init__(**kwargs)


class ConfirmationPopup(Popup):
    '''A popup to ask the user for confirmation (yes/no question)
    '''

    question_text = StringProperty()
    '''A yes/no question the user should answer
    '''

    on_user_choice_callback = ObjectProperty()
    '''Call this function when a the user chose a button. The callback is called
    with one boolean argument:
    - user_agreed: True/False according to the user's choice
    '''
    
    def __init__(self, **kwargs):
        # Act according to the desired file operation
        check_for_necessary_attributes(self, ['question_text', 'on_user_choice_callback'], kwargs)

        super(ConfirmationPopup, self).__init__(**kwargs)
        
    def on_user_choice(self, user_agreed):
        '''Act upon the user's choice
        '''
        self.on_user_choice_callback(user_agreed)
        self.dismiss()


class NotificationPopup(Popup):
    '''A popup to show information to the user. It has the option to dismiss
    itself automatically after a given time
    '''

    dismiss_timeout = NumericProperty(1)
    '''Max time (in seconds) before the popup is dismissed. If equals zero,
    the popup will wait for the user to dismiss the popup.
    '''

    def __init__(self, **kwargs):
        # Act according to the desired file operation
        check_for_necessary_attributes(self, ['text'], kwargs)

        kwargs['title']='Notification'
        kwargs['content'] = Label(text=kwargs['text'])
        kwargs['auto_dismiss']=True
        
        # Set the timer
        if self.dismiss_timeout:
            Clock.schedule_once(self.timer_expired, self.dismiss_timeout)
        
        super(NotificationPopup, self).__init__(**kwargs)
        
    def timer_expired(self, dt):
        '''Dismiss the popup if the timer expired
        '''
        self.dismiss()
        



########
# everything down here I'm not sure of
########

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
