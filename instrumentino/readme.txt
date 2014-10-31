Files:
instrumentino/						-
	readme.txt					- this file
	setup.py					- required for preparing a Python egg
	ez_setup.py					- required for preparing a Python egg

	instrumentino/					- contains the code
		__init__.py				- declares the main class: instrumenting.Instrument
		cfg.py					- configuration variables and functions
		comp.py					- defines the parent class for a component and its variables
		util.py					- utility functions
		action.py				- defines the parent class for an action
		executable_listctrl.py			- define ExecutableListCtrl: a class for a list controller, with add/remove/execute buttons
		method.py				- defines a method as a list of actions (inherit from ExecutableListCtrl)
		sequence.py				- defines a sequence as a list of saved methods (inherit from ExecutableListCtrl)
		log_graph.py				- handle data online visualization

		resources/				- resource directory
			__init__.py			- empty. required for preparing a Python egg
			main.xrc			- a GUI description file for the main window
			stopButton.png			- stop button icon
			uProcessDriver.dll		- LabSmith API
			uProcessDriver_C.dll		- C wrapper for the LabSmith API

		controllers/				- controllers
			__init__.py			- instrumentino.InstrumentinoController: parent class for a controller

			arduino/			- Arduino controlled components
				__init__.py		- the Arduino controller class and variables
				edaq.py			- components from eDAQ (recording systems)
				hvm.py			- components from HVM (high voltage controllers)
				mks.py			- components from MKS (mass flow controllers)
				parker.py		- components from Parker (pressure controllers)
				pins.py			- on/off pins for simple components
				spellman.py		- components from Spellman (high voltage controllers)
				tecan.py		- components from Tecan (SIA systems)

			labsmith_eib/			- LabSmith controlled components
				__init__.py		- the LabSmith controller class and variables
				labsmith_comps.py	- supported LabSmith components

	instrumentino.egg-info/				- egg description directory
		automatically created files…		- various files

	dist/						- the distribution directory
		instrumentino-1.0-py2.7.egg		- the egg file

