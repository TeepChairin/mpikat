#!/usr/bin/env python

import sys, getopt, time, os, threading, signal
sys.settrace

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GObject

#from atk import gobject_accessible_for_object



INIT_HEIGHT = 300
INIT_WIDHT = 600


#PACKETIZER_WIDHT = 1200
#RSC_WIDHT = 700

SESSION_NAME        = 0
SESSION_RSC         = 1
SESSION_PACKETIZER  = 2


KATCP_PORT = "7147"

sys.path = ["lib"] + sys.path
newSession = False
connectPacketizerHost = None
connectPacketizerPort = None
connectRcmHost = None
connectRcmPort = None

from connDialog import *
from rscClient import *
from packerClient import *
from rxsTabbed import *
from appConfig import *
from gb40Tool import *
from macroList import *


gb40_standlone = False
regTool_standalone=False
cmdTool_standalone = False
capTool_standalone = False

address = 0
length = 1
openPreset = None





    
class t_pyRxs(gtk.Window):
 

    def __init__(self, openPreset):
        super(t_pyRxs, self).__init__()
        
        self.sensorMonitorCounter = 0;
        
        self.height = INIT_HEIGHT;
        self.width = INIT_WIDHT;                       

    # Default Configuration
        self.sessionID = 0
        self.sessions = dict();
        
        self.clientID = 0
        
        self.rxs_Name = "RxS"
        self.rxs_rscHost = ""
        self.rxs_rscPort = 7147
        
        self.rxs_packerHost = ""
        self.rxs_packerPort = 7147
    
                      
    
    # Configuration File     
        home = os.getenv("HOME", False)
        if home:
            self.cfgFile = home + "/" + CFG
        else:
            self.cfgFile = os.getenv("HOMEDRIVE", "") + os.getenv("HOMEPATH", "nothing") + "\\" + CFG
        
        self.cfg = t_appConfig(self.cfgFile);
        self.cfg.updateFromFile();
        self.restoreEnvironment()
      
      # ConnectionDialog, Last Settings
        self.conDialogValues_read()
                
      # window creation
        self.set_title(APP)
        #self.connect("destroy", self.onExit)
        self.connect("delete_event", self.onDelete)
        #self.connect("hide", self.onHide)
        
      # external Kill Signale
        signal.signal(signal.SIGINT,  self.onSignalExit)
        signal.signal(signal.SIGTERM, self.onSignalExit)
        
        #self.set_position(gtk.WIN_POS_CENTER)
       
      #menuBar
        vbox = gtk.VBox(False)
        self.add(vbox)
        
        menuBar = gtk.MenuBar()
        vbox.pack_start(menuBar, False, False, 0)
        
      #progMenu
        progmenu = gtk.Menu()
        
        progm = gtk.MenuItem(APP)
        progm.set_submenu(progmenu)
        menuBar.append(progm)
       
        save = gtk.MenuItem("save environment")
        save.connect("activate", self.onSaveEnvironment)
        progmenu.append(save)
        
        progmenu.append(gtk.SeparatorMenuItem())
        
        exit = gtk.MenuItem("Exit")
        exit.connect("activate", self.onExit)
        progmenu.append(exit)
        
        
      #Client Menu        
        rxsMenu = gtk.Menu()
        rxsM = gtk.MenuItem("S-BandRx")
        rxsM.set_submenu(rxsMenu)
        
        rxsM_new = gtk.MenuItem("new")
        rxsM_new.connect("activate", self.menu_onNewRxs)
        rxsMenu.append(rxsM_new)
        
        rxsM_close = gtk.MenuItem("close")
        rxsM_close.connect("activate", self.menu_onCloseTab)
        rxsMenu.append(rxsM_close)
        menuBar.append(rxsM)
        

      # Tabbed View for Devices
        self.rxsTabbed = t_rxsTabbed();
        vbox.pack_start(self.rxsTabbed, True, True, 0);
    
      # open Sessions from cmd line selection or config File
        
        if connectRcmHost or connectPacketizerHost:
            
            name = ""
            if connectRcmHost:
                name += "%s:%d " % (connectRcmHost, connectRcmPort)
            if connectPacketizerHost:
                name += "%s:%d " % (connectPacketizerHost, connectPacketizerPort)
                
            self.session_connect(
                name,
                connectRcmHost,
                connectRcmPort,
                connectPacketizerHost,
                connectPacketizerPort)
        elif openPreset:
            print "open selected preset connection"
            self.openPreset(openPreset)
            
        elif not newSession:
            if not self.openSessionsFromAppCfg():
                self.menu_onNewRxs(None)
         
         
         
        
      # init done, show all 
        
        self.show_all()
        self.resize(self.width, self.height)
        
        GObject.idle_add(self.onIdle)
        
 
        #self.connect("size-request", self.onSizeRequest)
 
 

        
 
    def __del__(self):
        print "t_pyRxs.__del__():"
        self.cleanUp()
        
    
    #def onSizeRequest(self, widgete, requisition):
    #    self.width, self.height = self.get_size()
    #    print self.width, ", ", self.height
        
    
    def restoreEnvironment(self):
        #print "restoreEnvironment"
        for pSet in self.cfg.get_parameterSets("MainWindow"):
            if pSet.has_key("width"):
                self.width = int(pSet["width"])
            if pSet.has_key("height"):
                self.height = int(pSet["height"])
                
        
        

    def saveEnvironment(self):
        print "saveEnvironment"
        
        self.width, self.height = self.get_size()
        
        # first remove old values
        self.cfg.remove_sections("MainWindow")
        
        # create new values
        mainWinParams = dict()
        mainWinParams["width"] = self.width;
        mainWinParams["height"] = self.height;
        
        #store values in enviromnent
        self.cfg.add_parameterSet("MainWindow", mainWinParams)
        
            
            
            
            
    def cleanUp(self):
        
        print "cleanUp():"
    
        if self.sessionList_isCapturing():
            msg = gtk.MessageDialog(buttons=gtk.BUTTONS_OK_CANCEL)
            msg.set_markup("Active Data Capturing! Exiting anyway?")
            res = msg.run();
            msg.hide()
            del msg
            if res == gtk.RESPONSE_CANCEL:
                print "cleanUp() ABORTING"
                return False

           
     #save application data into file    
        # remove old Session Data from AppCfg
        self.cfg.remove_sections("Session")
        
        
       # recreate session configuration
        for S in self.sessionList_get_sessions():
            sessionData = self.sessionList_get_session(S)
            #print sessionData
            self.cfg.add_parameterSet("Session", sessionData)
            
            
        
      # recreate conDialog Entrys Data
        self.conDialogValues_write()
        self.rxsTabbed.destroy()
        
       
       # write current Session List to CfgFile
        self.saveEnvironment()
        self.cfg.writeToFile(self.cfgFile, APP); 
    
        return True
        
        
    def gb40Tool_onClose(self):
        print "gb40Tool_onClose"
 
    
           
    def plot_set_label(self, xLabel, yLabel):
        self.plot_xLabel = xLabel
        self.plot_yLabel = yLabel
                         

    def onIdle(self):
        gobject.idle_add(self.onIdle)
        time.sleep(0.01); # handover control to neigbour task
    
    def onSaveEnvironment(self, menu): 
        print "onSaveEnvironment()"
        
       # recreate session configuration
        self.cfg.remove_sections("Session")
        for S in self.sessionList_get_sessions():
            sessionData = self.sessionList_get_session(S)
            #print sessionData
            self.cfg.add_parameterSet("Session", sessionData)
            
      # recreate conDialog Entrys Data
        self.conDialogValues_write()
        self.saveEnvironment()
        self.cfg.writeToFile(self.cfgFile, APP); 
        
    def onExit(self, menu):
        print "t_pyRxs.onExit"
        if not self.cleanUp():
            return
            
        self.destroy()
        gtk.main_quit();

      
    def onDelete(self, x, y):
        print "t_pyRxs.onDelete"
        if not self.cleanUp():
            return True
        
            
        self.destroy()
        gtk.main_quit();
        return False
        

    def onSignalExit(self, sigNr, frame):
        print "t_pyRxs.onSignalExit():"
        if not self.cleanUp():
            return
        self.destroy()
        gtk.main_quit();

    
    def onHide(self, widget):
        print "t_pyRxs.onHide()"


                
    def errMsg(self, text):
        #msg = gtk.MessageDialog(type=gtk.MessageType.ERROR, buttons=gtk.BUTTONS_OK)
        msg = gtk.MessageDialog(type=gtk.MessageType.ERROR, buttons=gtk.ButtonsType.OK)
        msg.set_markup(text);
        msg.run();
        msg.destroy() 
        
        
    def addClient(self, cName, rsc, packetizer):
    
        self.sessionList_addSession(cName, rsc, packetizer)
        self.rxsTabbed.append_rxs(rsc, packetizer, gtk.Label(cName), self.tab_onCloseTab)              

        
        
   
    def onCloseTab(self, sessionID, page=None):
        
        print "onCloseTab()"
        if not page:
            page = self.rxsTabbed.get_current_page()

        #n = self.rxsTabbed.get_current_page()
       
        if self.sessions[sessionID][SESSION_RSC]:
            self.sessions[sessionID][SESSION_RSC].destroy()
        
        if self.sessions[sessionID][SESSION_PACKETIZER]:
            self.sessions[sessionID][SESSION_PACKETIZER].destroy()
        
  
        self.rxsTabbed.remove_page(page);
        self.sessionList_removeSession(sessionID)
    

    
    
    def onCloseTab_byWidget(self, sessionID, widget):
        print "onCloseTab_byWidget()"
       
        if self.sessions[sessionID][SESSION_RSC]:
            self.sessions[sessionID][SESSION_RSC].destroy()
        
        if self.sessions[sessionID][SESSION_PACKETIZER]:
            self.sessions[sessionID][SESSION_PACKETIZER].destroy()
        
  
        self.rxsTabbed.remove(widget);
        self.sessionList_removeSession(sessionID)
        

        
        
    
    
    def session_connect(self, name, rscHost, rscPort, packetizerHost, packetizerPort):
        
        rsc = None;
        packetizer = None;
        
        
        
        if( rscHost and rscPort):
            rsc = t_rscClient(name,
                              rscHost,
                              rscPort,
                              self.sessionList_getSessionID(),
                              self.clientID_next(),
                              self,
                              self.cfg)
                            
            if not rsc.openConnection():
                self.errMsg("RSC Connection '%s:%s' failed!" % (rscHost, rscPort));
                rsc.destroy();
                rsc = None
                return False
            
            rsc.show_all()
                        

        if( packetizerHost and packetizerPort ):         
            packetizer = t_packerClient(name,
                                        packetizerHost,
                                        packetizerPort,
                                        self.sessionList_getSessionID(),
                                        self.clientID_next(),
                                        self,
                                        self.cfg)
                                          
            if not packetizer.openConnection():
                self.errMsg("Packetizer Connection '%s:%s' failed!" % (packetizerHost, packetizerPort));
                packetizer.destroy()
                packetizer = None
                return False
                

            packetizer.signalConnect("onExit", self.onCloseTab)
            #self.width += PACKETIZER_WIDHT;
            
        if(rsc or packetizer): 
            self.addClient(name, rsc, packetizer); 
            #self.resize(self.width, self.height)
        
            
        
       
        return True       
        
    
    
        
        
            
    def menu_onNewRxs(self, menuItem):
                
        cDialog = t_connDialog(self.rxs_Name, self.rxs_rscHost, self.rxs_rscPort, self.rxs_packerHost, self.rxs_packerPort, self.cfg);
        
        ret = cDialog.run()
        (self.rxs_Name,
        self.rxs_rscHost, 
        self.rxs_rscPort, 
        self.rxs_packerHost, 
        self.rxs_packerPort) = cDialog.get_connection();
        cDialog.destroy();
        
        print "self.rxs_Name",       self.rxs_Name
        print "self.rxs_rscHost",    self.rxs_rscHost
        print "self.rxs_rscPort",    self.rxs_rscPort
        print "self.rxs_packerHost", self.rxs_packerHost
        print "self.rxs_packerPort", self.rxs_packerPort
        
        if not ret:
            return False            
        else:
            return self.session_connect(self.rxs_Name, self.rxs_rscHost, self.rxs_rscPort, self.rxs_packerHost, self.rxs_packerPort)
            

    
    def tab_onCloseTab(self, sessionId, widget):
        print "tab_onCloseTab:"
        self.onCloseTab_byWidget(sessionId, widget)    
    
    def menu_onCloseTab(self, menuItem):
        print "menu_onCloseTab()"
        n = self.rxsTabbed.get_current_page()

        packetizer = self.rxsTabbed.get_packetizer(n)
        if packetizer:
            self.onCloseTab(packetizer.getSessionID())
            return # one will destroy both if two. return
            
        rsc = self.rxsTabbed.get_rsc(n)
        if rsc:
            self.onCloseTab(rsc.getSessionID())
            return
        
         
           
    def sessionList_addSession(self, cName, rcm, packetizer):
        
        self.sessions[self.sessionID] = (cName, rcm, packetizer)
        self.sessionID += 1;
       
    
    def sessionList_isCapturing(self):
        for cName, rsc, packetizer in self.sessions.values():
            #print "Has Session", cName, "active capturing?"
            
            if rsc:
                if rsc.capTool:
                    return True
                    
            if packetizer:
                if packetizer.capTool:
                    return True
            
                if packetizer.signalMonitor.signalCaptureTool:
                    return True
                
        return False
        
        
    def sessionList_removeSession(self, sessionID):
        del self.sessions[sessionID]
        
        
    def sessionList_getSessionID(self):
        return self.sessionID
        
        
    def clientID_next(self):
        id = self.clientID
        self.clientID += 1;
        return id
        
        
    def sessionList_get_numSessions(self):
        return len(self.sessions)
        
    def sessionList_get_sessions(self):
        self.sensorMonitorCounter = 0;
        return self.sessions.values();
        
        
    def sessionList_get_session(self, Session):
        
        sData = dict()
        
        if Session[SESSION_NAME]:
            sData["Name"] = Session[0]
        
        if Session[SESSION_RSC]:
            sData["RSC-Host"] =  Session[SESSION_RSC].host
            sData["RSC-Port"] = Session[SESSION_RSC].port
            sData["RSC-ClientID"] = Session[SESSION_RSC].clientID
                                                    
        if Session[SESSION_PACKETIZER]:
            sData["Packetizer-Host"] = Session[SESSION_PACKETIZER].host
            sData["Packetizer-Port"] = Session[SESSION_PACKETIZER].port
            sData["Packetitzer-ClientID"] = Session[SESSION_PACKETIZER].clientID
           
        
        return sData

        """
            for mon in Session[SESSION_RSC].sensorMonitorDict.values():
                print "Mon:", mon
                sData["sensorMonitor"] = sensorMonitorCounter
                ensorMonitorCounter += 1

                iter = mon.SensorPropertieStore.get_iter_first()
                while iter:
                    print "  ", mon.SensorPropertieStore.get_value(iter, 0)
                    iter = mon.SensorPropertieStore.iter_next(iter)
                    
        """

    
    def sessionList_readFomAppCfg(self):
        
        cList = self.cfg.get_parameterSets("Session")
        
        # complete missing items
        for con in cList:
            if( not con.has_key("Name")):
                con["Name"] = ""
            if( not con.has_key("Packetizer-Host")):
                con["Packetizer-Host"] = ""
                
            if( not con.has_key("Packetizer-Port")):
                con["Packetizer-Port"] = KATCP_PORT
                
            if( not con.has_key("RSC-Host")):
                con["RSC-Host"] = ""
                 
            if( not con.has_key("RSC-Port")):
                con["RSC-Port"] = KATCP_PORT
                                                                   
        return cList  
        
        
    def sessionList_nSessions(self):
        cList = self.cfg.get_parameterSets("Session")
        return len(cList)         
        

        
    def getPreset(self, name):
        
        packetizerHost = None
        packetizerPort = None
        rscHost = None
        rscPort = None
        
        print "has ", name, "?"
        
        cList = self.cfg.get_parameterSets("PresetConnection")
        for pSet in cList:
            if pSet["Name"] == name:
                if pSet.has_key("RSC-Host"):
                    rscHost = pSet["RSC-Host"]
                    
                if pSet.has_key("RSC-Port"):
                    rscPort = pSet["RSC-Port"]
                    
                if pSet.has_key("Packetizer-Host"):
                    packetizerHost = pSet["Packetizer-Host"]
                    
                if pSet.has_key("Packetizer-Port"):
                    packetizerPort = pSet["Packetizer-Port"]
                
                return (rscHost, rscPort, packetizerHost, packetizerPort)
        
        msg = gtk.MessageDialog(buttons=gtk.BUTTONS_OK)
        msg.set_markup("No such preset '%s' found!" % (name))
        msg.run()
        msg.destroy()
            
        return (rscHost, rscPort, packetizerHost, packetizerPort)
                    
            
            
    def openPreset(self, name):
        rscHost, rscPort, packetizerHost, packetizerPort = self.getPreset(name)
        self.session_connect(name, rscHost, rscPort, packetizerHost, packetizerPort)
        return False
            
            
            
    def openSessionsFromAppCfg(self):
        
        if self.sessionList_nSessions() == 0:
            return False
        #print "open Sessions from File"
        for con in self.sessionList_readFomAppCfg():
            self.session_connect(con["Name"], con["RSC-Host"], con["RSC-Port"], con["Packetizer-Host"], con["Packetizer-Port"])
                                
                
        return True
    
    
    def conDialogValues_read(self):

        sets =  self.cfg.get_parameterSets("ConDialog")
        if sets:
            if sets[0].has_key('Name'):
                self.rxs_Name       = sets[0]['Name']
                
            if sets[0].has_key('RSC-Host'):
                self.rxs_rscHost    = sets[0]['RSC-Host']
            
            if sets[0].has_key('RSC-Port'):
                self.rxs_rscPort    = sets[0]['RSC-Port']
            
            if sets[0].has_key('Packetizer-Host'):
                self.rxs_packerHost = sets[0]['Packetizer-Host']
            
            if sets[0].has_key('Packetizer-Port'):
                self.rxs_packerPort = sets[0]['Packetizer-Port']
                    
 
        
    def conDialogValues_write(self):

        cdData = dict()
        if len(self.rxs_Name):
            cdData['Name'] = self.rxs_Name
            
        if len(self.rxs_rscHost):
            cdData['RSC-Host'] = self.rxs_rscHost
                        
        if len(self.rxs_rscPort):
            cdData['RSC-Port'] = self.rxs_rscPort            
        
        if len(self.rxs_packerHost):
            cdData['Packetizer-Host'] = self.rxs_packerHost
                        
        if len(self.rxs_packerPort):
            cdData['Packetizer-Port'] = self.rxs_packerPort

                  
        self.cfg.remove_sections("ConDialog")
        self.cfg.add_parameterSet("ConDialog", cdData)
        
        
        







           


class t_katcpCmdToolStandAlone(t_katcpCmdTool):

    def __init__(self, init, deviceType="unknown"):
        
        self.katcp = None;
        
        try:
            host, port = init.split(':')
        except:
            host = init
            port = DEFAULT_KATCP_PORT

        print "Connection:", host, ", ", port
        
    # Configuration File     
        home = os.getenv("HOME", False)
        if home:
            self.cfgFile = home + "/" + CFG
        else:
            self.cfgFile = os.getenv("HOMEDRIVE", "") + os.getenv("HOMEPATH", "nothing") + "\\" + CFG
        
        cfg = t_appConfig(self.cfgFile);
        cfg.updateFromFile();    
        
                
        katcp = t_rxsKatcp("KATCP-Cmd", host, port, deviceType)            
        ret = katcp.start()
        
        if not katcp.wait_connected(CONNECTIONTIMEOUT):
            self.onClose()
        
       # external Kill Signale
        signal.signal(signal.SIGINT,  self.onSignalExit)
        signal.signal(signal.SIGTERM, self.onSignalExit)
                
        #super(t_katcpCmdToolStandAlone, self).__init__(self.katcp, None, self.onClose)
        macroList = t_macroList(cfg, None, katcp)
        t_katcpCmdTool.__init__(self, katcp, None, self.onClose, cfg, macroList, None)
        
        
        
        
    def onClose(self):
        print "t_katcpCmdToolStandAlone.onClose"
        if self.katcp:
            self.katcp.stop()
            self.katcp.join()
            gtk.main_quit();
            
        self.destroy()
        
    def onSignalExit(self, sigNr, frame):
        print "onSignalExit():"
        t_katcpCmdTool.onClose(self, 0)
   




class t_registerToolStandAlone(t_registerTool):
    
    def __init__(self, init, address=0, length=1, deviceType="unknown"):
        
        try:
            host, port = init.split(':')
        except:
            host = init
            port = DEFAULT_KATCP_PORT
            
           
        
        self.katcp = t_rxsKatcp("Register Tool", host, port, deviceType)
        self.katcp.start()
        if not self.katcp.wait_connected(CONNECTIONTIMEOUT):
            self.onClose(None, None)
        
       # external Kill Signale
        signal.signal(signal.SIGINT,  self.onSignalExit)
        signal.signal(signal.SIGTERM, self.onSignalExit)
                
        super(t_registerToolStandAlone, self).__init__(None, self.katcp, address, length, self.onClose)
        
        self.onReadRegister(None)
        
        
      
    def onClose(self, start, stop):
        self.katcp.stop()
        self.katcp.join()
        self.destroy()
        
        gtk.main_quit();
        self.destroy()
        
    def onSignalExit(self, sigNr, frame):
        print "onSignalExit():"
        self.onClose(None, None);
         
                





class t_gb40gStandAlone(t_gb40Tool):
    
    def __init__(self, server, deviceType="unknown"):
        
        try:
            host, port = server.split(':')
        except:
            host = server
            port = DEFAULT_KATCP_PORT
            
        self.katcp = t_rxsKatcp("40GB/s-IFace", host, port, deviceType)
        self.katcp.start()
        
        if not self.katcp.wait_connected(CONNECTIONTIMEOUT):
            self.onClose()
                    
        super(t_gb40gStandAlone, self).__init__(None, self.katcp, self.onClose, server)
      
       # external Kill Signale
        signal.signal(signal.SIGINT,  self.onSignalExit)
        signal.signal(signal.SIGTERM, self.onSignalExit)     
        
        
           
      
    def onClose(self):
        self.katcp.stop()
        self.katcp.join()
        self.destroy()
        gtk.main_quit();
        sys.exit(0)


    def onSignalExit(self, sigNr, frame):
        print "onSignalExit():"
        self.onClose()
        

        
    
def viewHelp():
    
    print ""
    print "  usage: pyRxs [OPTS]"
    print ""
    print "  OPTS:"
    print "  ====="
    print ""
    print "    -p | --preset <PRESET> ...... Select a Preselected Connection"
    print "    -n | --new .................. New Session." 
    print "                                  Do not reestablich previous Session"
    print "    -P || --packetizer <HOST> ... create connection to packetizer <HOST>"
    print "    -R || --rcm <HOST> .......... create connection to receiverController <HOST>"
    print ""
    print "    --help, -h .................. showing this."
    print "    --cmd <IP[:port]> ........... Run the KATCP-Command Tool only"
    print "    --40g <IP[:port]> ........... Run the 40Gb.Iface Tool only"
    print "    --reg <IP[:PORT]> ........... Run the Rigister Tool only"
    print "                                  Default-Port:", DEFAULT_KATCP_PORT
    print "                                  Use --addr <ADDR> --len <LEN>"
    print "                                  to define reading range."
    print ""
        


     

# cmd line options
try:
    opts, args = getopt.getopt(
                    sys.argv[1:],
                     "hnp:R:P:",
                      ["help",
                       "cmd=",
                       "40gb=",
                       "reg=",
                       "addr=",
                       "len=",
                       "preset=",
                       "new",
                       "packetizer=",
                       "rcm="])

except getopt.GetoptError as err:
    # print help information and cleanUp:
    print str(err) # will print something like "option -a not recognized"
    # usage()
    sys.exit(2)  

for o, a in opts:                
    if o in ("-h", "--help"):
        viewHelp()
        sys.exit()
    
    elif o in ("-p", "--preset"):
        openPreset = a
        
    elif o in ("-n", "--new"):
        newSession = True
        
    elif o in ("-P", "--packetizer"):
        newSession = True
        try:
            connectPacketizerHost, connectPacketizerPort = a.split(':')
            connectPacketizerPort = int(connectPacketizerPort)
        except:
            connectPacketizerHost = a
            connectPacketizerPort = DEFAULT_KATCP_PORT
        
    elif o in ("-R", "--rcm"):
        newSession = True
        try:
            connectRcmHost, connectRcmPort = a.split(':')
            connectRcmPort = int(connectRcmPort);
        except:
            connectRcmHost = a
            connectRcmPort = DEFAULT_KATCP_PORT
        
    elif o == "--40gb":
        gb40_standlone = a
    
    elif o == "--reg":
        regTool_standalone = a
    
    elif o == "--cmd":
        cmdTool_standalone = a
    
    elif o == "--addr":
        try:
            address = int(a, 10)
        except:
            address = int(a,16)
        
    elif o == "--len":
        try:
            length = int(a, 10)
        except:
            length = int(a,16)
        
    else:
        print "unhandled option"  
        sys.exit(-1);
        
     
#print "connectPacketizerHost:", connectPacketizerHost
#print "connectPacketizerPort:", connectPacketizerPort
#print "connectRcmHost:", connectRcmHost
#print "connectRcmPort:",  connectRcmPort
        
if gb40_standlone:
    t_gb40gStandAlone(gb40_standlone)
elif regTool_standalone:
    t_registerToolStandAlone(regTool_standalone, address, length)
elif cmdTool_standalone:
    t_katcpCmdToolStandAlone(cmdTool_standalone)
elif capTool_standalone:
    t_captureToolStatdAlone(capTool_standalone)
else:        
    t_pyRxs(openPreset)
    
gtk.main()
