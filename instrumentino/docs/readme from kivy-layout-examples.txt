##########
# yoelk: ScreenManager 6
##########
- I had some problem with including garden folders, so I installed what's needed directly into the application folder
(see http://stackoverflow.com/questions/24048350/kivy-garden-in-pyinstaller-stuck-trying-to-trace-import)

- I wanted the side-menu to not necessarily take up all of the screen size (vertical), so I forked Garden.NavigationDrawer to let users control the side-menu height.
I also posted a pull request to the authors, I hope they accept it.
So for now it's good to have the garden parts installed locally in our library.

- Instead of having checkboxes and buttons, I turned to use ToggleButtons, but I found out they only support 1 button preesed in any time.
So I decided to create ToggleButtonMulti, a new button type that allows more than one button to be pressed.

- I changed a bit the GUI:
+ made a dynamic widget called 'ViewChooser' to reduce code duplication and add them from the python code according to the screen names.
+ changed some screen names
+ removed the user's log from the side-menu. Instead I envoke it (as a popup) by pressing the bottom activity line.
+ add support for 2 and 3-way split screens, with auto-rotation (try playing with the screen sizes when in split mode)


Issue #1: Some sizes would be better absolute (size_y instead of size_hint_y).
For example, the bottom buttons line should have the same size on all devices, and not proportional to the screen.
The same for the buttons in the side-menu.
Until now I couldn't get it to work. 

##########
# snarfums: comments/ideas
##########
Continuing from ScreenManager4

!!! ISSUES !!!
Issue #1: There is a known bug in garden.Graph that may only affect kivy 1.9? See https://github.com/kivy-garden/garden.graph/issues/7 . The fix is to change line 146 of __init__.py in garden.Graph

Issue #2: "Save Graph/Chart" button only works properly with kivy 1.9, otherwise this should run in 1.8?

New examples added:
- Menu: Checkboxes added for screens to be added to primary "DashBoard" Screed
  Note: Checkboxes do not actually do anything
- Menu-> Commands/Signals has live Charting example
  - Can save Chart to png file
  - Chart updates via ClockTick, which can be used to test other widget data updates
- Menu-> Log contains data
- Added graphic to "Stop" for graphics testing
- Cleaned up settings panels.
- Menu-> Methods/Sequences: Filechooser kinda works. Chooses correct files based on extension
  Note: Will not load or save any files, but methods exist for them

# Additional installation requirements
You will need to install:
garden.NavigationDrawer
garden.Graph

The notes on the commands I used to install the garden (on Ubuntu 14.x) and the garden.navigationdrawer are:

# Install pip (Python package manager): https://pip.pypa.io/en/latest/installing.html
sudo apt-get install python-pip

# Install kivy-garden: http://kivy.org/docs/api-kivy.garden.html
sudo pip install kivy-garden

# Search: Should return a list and one entry is "navigationdrawer"
gerden search

# Install navigationdrawer
sudo garden install navigationdrawer

# Install graph
sudo garden install graph

# Note: It's possible I had to install the garden as an admin user using sudo, then again as my non-admin user.  

##########
# yoelk: comments/ideas (from Screenmanager4)
##########
There are 4 different screens to present as I see it:
- Direct control of components
- Automation (method/sequence)
- User's log (textual)
- Signal log

I guess it doesn't make much sense to divide a Desktop screen to more than 3 parts, so I suggest that we support:
- single screen
- 2 parts *
- 3 parts *
* support these modes for screens of minimum size.

The user can decide which screens he wants to see and how many by checking checkboxes in the View menu.

The view menu can be a small button near the stop button and an activity feed line.
For devices that have small screens, we can use the same menu to show "File", "Comm" etc.

Big screen devices can have the natural menus on the top, though I don't know if Kivy lets you create them.
Maybe we'd need to make our own menubar, on the top or bottom. Maybe even add an auto-hide option.

##########
# snarfums: comments/ideas
##########
Lots of ugly in this example. Just trying things out and get all the major areas covered with something simple to evaluate. 
