# ** Section ** Imports
from temod.base.entity import Entity
from temod.base.attribute import *
from copy import deepcopy
# ** EndSection ** Imports


# ** Section ** Entity_DockerContainer
class DockerContainer(Entity):
	ENTITY_NAME = "dockerContainer"
	ATTRIBUTES = [
		{"name":"id","type":StringAttribute, "required":True, "max_length": 64, "is_id":True,"is_nullable":False},
		{"name":"name","type":StringAttribute, "required":True, "non_empty": True, "is_nullable": False, "max_length":100},
		{"name":"image","type":StringAttribute, "required":True, "non_empty": True, "is_nullable": False, "max_length":100}
	]
# ** EndSection ** Entity_DockerContainer