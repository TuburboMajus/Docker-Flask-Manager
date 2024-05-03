# ** Section ** Imports
from temod.base.entity import Entity
from temod.base.attribute import *
from copy import deepcopy
# ** EndSection ** Imports


# ** Section ** Entity_DockerComposition
class DockerComposition(Entity):
	ENTITY_NAME = "dockerComposition"
	ATTRIBUTES = [
		{"name":"id","type":UUID4Attribute, "required":True,"is_id":True,"is_nullable":False},
		{"name":"volumes_path","type":StringAttribute, "required": True, "max_length":300, "is_nullable":False},
		{"name":"name","type":StringAttribute, "required":True, "non_empty": True, "is_nullable": False, "max_length":100},
		{"name":"version","type":StringAttribute, "required":True, "non_empty": True, "is_nullable": False, "max_length":50}
	]
# ** EndSection ** Entity_DockerComposition


# ** Section ** Entity_DockerCompositionContainer
class DockerCompositionContainer(Entity):
	ENTITY_NAME = "dockerCompositionContainer"
	ATTRIBUTES = [
		{"name":"composition","type":UUID4Attribute, "required":True, "is_id":True,"is_nullable":False},
		{"name":"container","type":StringAttribute, "required": True, "is_id":True, "max_length":64, "is_nullable":False}
	]
# ** EndSection ** Entity_DockerCompositionContainer


# ** Section ** Entity_DockerComposeOrder
class DockerComposeOrder(Entity):
	ENTITY_NAME = "dockerComposeOrder"
	ATTRIBUTES = [
		{"name":"id","type":UUID4Attribute, "required":True,"is_id":True,"is_nullable":False},
		{"name":"composition","type":UUID4Attribute, "required": True, "is_nullable":False},
		{"name":"cmd","type":StringAttribute, "required":True, "non_empty": True, "is_nullable": False, "max_length":50},
		{"name":"args","type":StringAttribute, "max_length":300},
		{"name":"status","type":StringAttribute, "max_length":20},
	]
# ** EndSection ** Entity_DockerComposeOrder