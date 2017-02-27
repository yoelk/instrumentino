
See http://kivy-garden.github.io/garden.filebrowser/index.html


FileBrowser
===========

The ``FileBrowser`` widget is an advanced file browser. You use it
similarly to FileChooser usage.

It provides a shortcut bar with links to special and system directories.
When touching next to a shortcut in the links bar, it'll expand and show
all the directories within that directory. It also facilitates specifying
custom paths to be added to the shortcuts list.

It provides a icon and list view to choose files from. And it also accepts
filter and filename inputs.

To create a ``FileBrowser`` which prints the currently selected file as 
well as the current text in the filename field when 'Select' is pressed,
with a shortcut to the Documents directory added to the favorites bar:

.. code-block:: python

    ffrom kivy.app import App
    from os.path import sep, expanduser, isdir, dirname

    class TestApp(App):

        def build(self):
            if platform == 'win':
                user_path = dirname(expanduser('~')) + sep + 'Documents'
            else:
                user_path = expanduser('~') + sep + 'Documents'
            browser = FileBrowser(select_string='Select',
                                  favorites=[(user_path, 'Documents')])
            browser.bind(
                        on_success=self._fbrowser_success,
                        on_canceled=self._fbrowser_canceled)
            return browser

        def _fbrowser_canceled(self, instance):
            print 'cancelled, Close self.'

        def _fbrowser_success(self, instance):
            print instance.selection

    TestApp().run()

Events
------

- ``on_canceled``
  Fired when the `Cancel` buttons `on_release` event is called.
- ``on_success``
  Fired when the `Select` buttons `on_release` event is called.

License
=======

Same license as kivy (currently MIT License).
