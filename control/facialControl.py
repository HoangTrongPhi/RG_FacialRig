
import maya.cmds as cmds
import maya.mel as mel

import sys
import os
import json

from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance

from PySide2 import QtUiTools, QtCore, QtGui, QtWidgets
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile, QIODevice
from PySide2.QtWidgets import QApplication, QWidget, QMainWindow, QFileDialog
from PySide2.QtGui import QPixmap, QIcon
from PySide2.QtCore import QObject, Qt

import importlib
import model.explorePath as explorePath
importlib.reload(explorePath)

import model.teleMayaMaxModel as teleMayaMaxModel
#import model.teleMaxMaya as teleMaxMayaModel
importlib.reload(teleMayaMaxModel)

from functools import partial

try:
    from shiboken2 import wrapInstance
    from maya import OpenMayaUI as omui

    omui.MQtUtil.mainWindow()
    ptr = omui.MQtUtil.mainWindow()

    try:
        reload(teleMayaMaxModel)
    except:
        importlib.reload(teleMayaMaxModel)

    cmds.loadPlugin('fbxmaya.mll', quiet=True)  # very important
    print('Import Success Maya Module')
except:
    print('ERROR: Import Maya Module')


def getDirectoryofModule(modulename):

    #Input: module as string
    #OUtput:
        #List: name as string and directory of module

    module = modulename
    try:
        module = importlib.import_module(modulename)
    except:
        pass

    currWD = CommonPyFunction.Get_WD(module.__file__)
    return currWD




this_file_directory = os.path.dirname(__file__)
main_directory = os.path.dirname(this_file_directory)

#data = os.path.dirname(this_file_directory) + r"\model\data"
#UI_Path = os.path.dirname(this_file_directory) + r"\UI\Teleport_UI.ui"
### icon path
#iconPerry = os.path.dirname(this_file_directory) + r"\UI\icons\Perry.png"
#iconAgentP = os.path.dirname(this_file_directory) + r"\UI\icons\AgentP.png"
#iconSupport = os.path.dirname(this_file_directory) + r"\UI\icons\needPhineasHelp.png"
#iconFindToolWhere = os.path.dirname(this_file_directory) + r"\UI\icons\findToolWhere.png"
#iconGuide = os.path.dirname(this_file_directory) + r"\UI\icons\guide.png"
#iconNeedPhineasHelp = os.path.dirname(this_file_directory) + r"\UI\icons\needPhineasHelp.png"

#iconImportUE = os.path.dirname(this_file_directory) + r"\UI\icons\importUE.png"
#iconExPortUE = os.path.dirname(this_file_directory) + r"\UI\icons\exportUE.png"
#iconSharingUE = os.path.dirname(this_file_directory) + r"\UI\icons\sharingUE.png"
#iconUploadUE = os.path.dirname(this_file_directory) + r"\UI\icons\uploadUE.png"


#####

class teleportUI(QtWidgets.QWidget):
    window = None  # đang rỗng

    def __init__(self, parent=None):
        """
        Initialize class.

        """
        #initialize window and load UI file
        super(teleportUI, self).__init__(parent=parent)

        ##

        self.createWidgets()
        self.createConnection()

        #self.browseFolderPath()
        #self.updateFolderPath()
        #self.fixMayaPath()



    def createWidgets(self):

        self.checkerBoxOpt = QtWidgets.QAbstractButton
        self.setWindowFlags(QtCore.Qt.Window)
        self.widget = QtUiTools.QUiLoader().load(UI_Path)
        self.widget.setParent(self)
            # set initial window size
        self.setFixedSize(460, 920)

        self.perry = self.widget.findChild(QtWidgets.QPushButton, "perry")
        self.perry.setIcon(QtGui.QIcon(iconPerry))

        self.agentP = self.widget.findChild(QtWidgets.QPushButton, "agentP")
        self.agentP.setIcon(QtGui.QIcon(iconAgentP))

        self.findToolWhere = self.widget.findChild(QtWidgets.QPushButton, "findToolWhere")
        self.findToolWhere.setIcon(QtGui.QIcon(iconFindToolWhere))

        self.guide = self.widget.findChild(QtWidgets.QPushButton, "guide")
        self.guide.setIcon(QtGui.QIcon(iconGuide))

        self.needPhineasHelp = self.widget.findChild(QtWidgets.QPushButton, "needPhineasHelp")
        self.needPhineasHelp.setIcon(QtGui.QIcon(iconNeedPhineasHelp))

        ## btn UE
        self.Import_UE = self.widget.findChild(QtWidgets.QPushButton, "Import_UE")
        self.Import_UE.setIcon(QtGui.QIcon(iconImportUE))

        self.Export_UE = self.widget.findChild(QtWidgets.QPushButton, "Export_UE")
        self.Export_UE.setIcon(QtGui.QIcon(iconExPortUE))

        self.upload_UE = self.widget.findChild(QtWidgets.QPushButton, "upload_UE")
        self.upload_UE.setIcon(QtGui.QIcon(iconUploadUE))

        self.sharing_UE = self.widget.findChild(QtWidgets.QPushButton, "sharing_UE")
        self.sharing_UE.setIcon(QtGui.QIcon(iconSharingUE))


        # locate UI widgets

        #Intro
        self.perry = QtWidgets.QPushButton("Perry")
        self.agentP = QtWidgets.QPushButton("Agent")
        self.findToolWhere = QtWidgets.QPushButton("FindToolWhere")
        self.guide = QtWidgets.QPushButton("Guide")

        ### Maya <-> Max
        self.getPathFile = self.widget.findChild(QtWidgets.QLineEdit, "getPathFile")

        self.explorePath = self.widget.findChild(QtWidgets.QPushButton, "explorePath")
        self.savePathFile = self.widget.findChild(QtWidgets.QPushButton, "savePathFile")

        self.progressBar = self.widget.findChild(QtWidgets.QProgressBar)
        self.progressBar.setValue(0)
        self.type_FBX = self.widget.findChild(QtWidgets.QRadioButton, "type_FBX")
        self.type_USD = self.widget.findChild(QtWidgets.QRadioButton, "type_USD")
        self.type_IMG = self.widget.findChild(QtWidgets.QRadioButton, "type_IMG")

        self.Import = self.widget.findChild(QtWidgets.QPushButton, "Import")
        self.Export = self.widget.findChild(QtWidgets.QPushButton, "Export")
        self.allScene = self.widget.findChild(QtWidgets.QPushButton, "allScene")
        self.exOther = self.widget.findChild(QtWidgets.QPushButton, "exOther")

        self.Take = self.widget.findChild(QtWidgets.QPushButton, "Take")
        self.Give = self.widget.findChild(QtWidgets.QPushButton, "Give")
        ###
        #######  Maya <-> UnrealEngine5
        self.Import_UE = self.widget.findChild(QtWidgets.QPushButton, "Import_UE")
        self.Export_UE = self.widget.findChild(QtWidgets.QPushButton, "Export_UE")
        self.Sharing_UE = self.widget.findChild(QtWidgets.QPushButton, "Sharing_UE")
        self.upload_UE = self.widget.findChild(QtWidgets.QPushButton, "upload_UE")

        ## need Phineas help
        self.needPhineasHelp = QtWidgets.QPushButton("NeedPhineasHelp")


        # Assign functionally to buttons
    def createConnection(self):


        """
        Your code goes here
        """
    def getExplorePath(self):
        explorePath.ExplorePath()
        #return folder





def openWindow():  # Create UI

    """
    ID Maya and attach tool window.
    """

    if QtWidgets.QApplication.instance():
        # Id any current instances of tool and destroy
        for win in QtWidgets.QApplication.allWindows():
        #for win in QtWidgets.QApplication.allWindows():
            if "MainWindow" in win.objectName():
                win.destroy()

    # QtWidgets.QApplication(sys.argv)
    mayaMainWindowPtr = omui.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(int(mayaMainWindowPtr), QtWidgets.QWidget)
    teleportUI.window = teleportUI(parent=mayaMainWindow)
    teleportUI.window.setObjectName("MainWindow")
    teleportUI.window.setWindowTitle("RG_FacialRig")
    teleportUI.window.show()

openWindow()


