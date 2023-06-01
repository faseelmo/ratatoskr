import xml.etree.ElementTree as ET
from xml.dom import minidom

def prettyPrint(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

#########################################################################
""" Model Parameters """
memory_nodes = range(0, 16)    # where the memory should map on the mesh
cpu_nodes = range(16, 22)      # where the cpu should map on the mesh
#########################################################################
""" Root Node """
map_data = ET.Element('map')
#########################################################################
""" Sender Nodes Binding """
for i in range(0, len(memory_nodes)):
    bind = ET.SubElement(map_data, 'bind')

    task = ET.SubElement(bind, 'task')
    task.set('value', str(i))

    node = ET.SubElement(bind, 'node')
    node.set('value', str(memory_nodes[i]))
#########################################################################
""" Receiver Nodes Binding """
for i in range(0, len(cpu_nodes)):
    bind = ET.SubElement(map_data, 'bind')

    task = ET.SubElement(bind, 'task')
    task.set('value', str(len(memory_nodes) + i))

    node = ET.SubElement(bind, 'node')
    node.set('value', str(cpu_nodes[i]))
##########################################################################
""" Write data to xml file """
senders_file = open('map.xml', 'w')
senders_file.write(prettyPrint(map_data))
senders_file.close()
