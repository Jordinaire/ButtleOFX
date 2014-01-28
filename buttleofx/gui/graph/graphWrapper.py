from PyQt5 import QtCore
import logging
# quickmamba
from quickmamba.models import QObjectListModel
# gui
from buttleofx.gui.graph.node import NodeWrapper
from buttleofx.gui.graph.connection import ConnectionWrapper


class GraphWrapper(QtCore.QObject):
    """
        Class GraphWrapper defined by:
            - _view : to have the view object

            - _nodeWrappers : list of node wrappers (the python objects we use to communicate with the QML)
            - _connectionWrappers : list of connections wrappers (the python objects we use to communicate with the QML)

            - _zMax : to manage the depth of the graph (in QML)

            - _graph : the name of the graph mapped by the instance of this class.

        This class is a view (= a map) of a graph.
    """
    
    _resize = False

    def __init__(self, graph, view):
        super(GraphWrapper, self).__init__(view)

        self._view = view
        print ("view", view)

        self._nodeWrappers = QObjectListModel(self)
        self._connectionWrappers = QObjectListModel(self)

        self._zMax = 2

        self._graph = graph

        # links core signals to wrapper layer
        self._graph.nodesChanged.connect(self.updateWrappers)
        self._graph.connectionsChanged.connect(self.updateConnectionWrappers)  
        
        self.tmpMoveNode = [0,0]

        logging.info("Gui : GraphWrapper created")

    def __str__(self):
        """
            Displays on terminal some data.
            Usefull to debug the class.
        """
        str_list = []

        str_list.append("=== Graph Buttle Wrapper === \n")
        str_list.append("---- all nodeWrappers ---- \n")

        for nodeWrapper in self._nodeWrappers:
            str_list.append(nodeWrapper.__str__())
            str_list.append("\n")

        str_list.append("---- all connectionWrappers ---- \n")
        for con in self._connectionWrappers:
            str_list.append(con.__str__())
            str_list.append("\n")

        str_list.append((self.getGraphMapped()).__str__())

        return ''.join(str_list)
               
    @QtCore.pyqtSlot(int, result=float)
    def maxHeight(self, height):
        """
            Browse all the nodes to calculate a height based on the extreme coordinates
        """
        max = height
        min = 0
        for nodeWrapper in self._nodeWrappers:
            if(max < nodeWrapper.yCoord):
              max = nodeWrapper.yCoord
            if(min > nodeWrapper.yCoord):
              min = nodeWrapper.yCoord
        return max - min
        
    @QtCore.pyqtSlot(int, result=float)
    def maxWidth(self, width):
        """
            Browse all the nodes to calculate a width based on the extreme coordinates
        """
        max = width
        min = 0
        for nodeWrapper in self._nodeWrappers:
            if(max < nodeWrapper.xCoord):
              max = nodeWrapper.xCoord
            if(min > nodeWrapper.xCoord):
              min = nodeWrapper.xCoord
        return max - min
        
    @QtCore.pyqtSlot(int, int, result=QtCore.QObject)    
    def fitInScreenSize(self, width, height):
        """
            Calculate average coordinates of all the nodes to center the graph in the screen
        """
        coords = QObjectListModel(self)
        averageX = 0
        averageY = 0
        cpt = 0
        for nodeWrapper in self._nodeWrappers:
            averageX += nodeWrapper.xCoord
            averageY += nodeWrapper.yCoord
            cpt += 1
        averageX = averageX / cpt
        averageY = averageY / cpt  
        heightCoeff = height/self.maxHeight(height)
        widthCoeff = width/self.maxWidth(width)
        if(heightCoeff < widthCoeff):
            zoomCoeff = height / self.maxHeight(height) 
        else:
            zoomCoeff = width / self.maxWidth(width) 
        
        coords.append(averageX)
        coords.append(averageY)
        coords.append(zoomCoeff)
        
        return coords

    ################################################## ACCESSORS ##################################################

    #################### getters ####################

    def getGraphMapped(self):
        """
            Returns the graph (the node list and the connection list), mapped by this graphWrapper.
        """
        return self._graph

    def getNodeWrappers(self):
        """
            Returns the nodeWrapper list.
        """
        return self._nodeWrappers

    @QtCore.pyqtSlot(str, result=QtCore.QObject)
    def getNodeWrapper(self, nodeName):
        """
            Returns the right nodeWrapper, identified with its nodeName.
        """
        for nodeWrapper in self._nodeWrappers:
            if nodeWrapper.getName() == nodeName:
                return nodeWrapper
        return None  # QtCore.QObject(self)
        
    @QtCore.pyqtSlot(QtCore.QObject, bool, result=QtCore.QObject)
    def getConnectedClipWrapper(self, clipWrapper, disable):
        """
            Returns the clip connected to an input clip if it exists.
        """
        for connection in self._connectionWrappers:
            if((clipWrapper.getNodeName() == connection.getIn_clipNodeName() and clipWrapper.getClipName() == connection.getIn_clipName())):
                if(disable):
                    connection.setEnabled(False)
                connection.currentConnectionStateChanged.emit()
                return self.getNodeWrapper(connection.out_clipNodeName).getClip(connection.out_clipName)
                
        return None

    def getConnectionWrappers(self):
        """
            Returns the connectionWrapper list.
        """
        return self._connectionWrappers

    def getConnectionWrapper(self, connectionId):
        """
            Returns a connectionWrapper given a connection id.
        """
        for connection in self._connectionWrappers:
            if connection.getId() == connectionId:
                return connection
        return None

    @QtCore.pyqtSlot(result=QtCore.QObject)
    def getLastCreatedNodeWrapper(self):
        """
            Returns the wrapper of the last node created.
        """
        return self._nodeWrappers[-1]
        
    @QtCore.pyqtSlot(result=float)
    def getTmpMoveNodeX(self):
        return self.tmpMoveNode[0]
        
    @QtCore.pyqtSlot(result=float)
    def getTmpMoveNodeY(self):
        return self.tmpMoveNode[1]

    def getZMax(self):
        """
            Returns the depth of the QML graph
        """
        return self._zMax
        
    def resize(self):
        return self._resize

    #################### setters ####################
    
    def setResize(self, value):
        self._resize = value
        self.currentSizeChanged.emit()
    
    @QtCore.pyqtSlot(str)
    def setTmpMoveNode(self, name):
        node = self.getNodeWrapper(name)
        self.tmpMoveNode[0] = node.xCoord
        self.tmpMoveNode[1] = node.yCoord
    
    def setTmpMoveNodeX(self, value):
        self.tmpMoveNode[0] = value
     
    def setTmpMoveNodeY(self, value):
        self.tmpMoveNode[1] = value
        
    def setZMax(self, zMax):
        """
            Sets the depth of the QML graph
        """
        self._zMax = zMax

    ################################################## CREATIONS ##################################################

    def createNodeWrapper(self, nodeName):
        """
            Creates a node wrapper and add it to the nodeWrappers list.
        """
        # we search the right node in the node list
        node = self._graph.getNode(nodeName)
        if node:
            nodeWrapper = NodeWrapper(node, self._view)
            self._nodeWrappers.append(nodeWrapper)

    def createConnectionWrapper(self, connection):
        """
            Creates a connection wrapper and add it to the connectionWrappers list.
        """
        conWrapper = ConnectionWrapper(connection, self._view)
        self._connectionWrappers.append(conWrapper)

    ################################################ UPDATE WRAPPER LAYER ################################################

    def updateWrappers(self):
        self.updateNodeWrappers()
        self.updateConnectionWrappers()
        
    def updateNodeWrappers(self):
        """
            Updates the nodeWrappers when the signal nodesChanged has been emitted.
        """
        # we clear the list
        self.getNodeWrappers().clear()
        # and we fill with the new data
        for node in self._graph.getNodes():
            self.createNodeWrapper(node.getName())

    def updateConnectionWrappers(self):
        """
            Updates the connectionWrappers when the signal connectionsChanged has been emitted.
        """
        # we clear the list
        self.getConnectionWrappers().clear()
        # and we fill with the new data
        for connection in self._graph.getConnections():
            self.createConnectionWrapper(connection)

    ################################################## DATA EXPOSED TO QML ##################################################

    # nodeWrappers and connectionWrappers
    nodeWrappers = QtCore.pyqtProperty(QtCore.QObject, getNodeWrappers, constant=True)
    connectionWrappers = QtCore.pyqtProperty(QtCore.QObject, getConnectionWrappers, constant=True)

    # z index for QML (good superposition of nodes in the graph)
    zMaxChanged = QtCore.pyqtSignal()
    zMax = QtCore.pyqtProperty(int, getZMax, setZMax, notify=zMaxChanged)
    
    currentSizeChanged = QtCore.pyqtSignal()
    resize = QtCore.pyqtProperty(bool, resize, notify=currentSizeChanged)
