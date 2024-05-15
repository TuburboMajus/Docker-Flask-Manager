# ** Section ** Imports
from temod.base.entity import Entity
from temod.base.attribute import *
from copy import deepcopy
# ** EndSection ** Imports


# ** Section ** Entity_NginxOrder
class NginxOrder(Entity):
	ENTITY_NAME = "nginxOrder"
	ATTRIBUTES = [
		{"name":"id","type":UUID4Attribute, "required":True,"is_id":True,"is_nullable":False},
		{"name":"cmd","type":StringAttribute, "required": True, "max_length":20, "is_nullable":False},
		{"name":"baseconf","type":StringAttribute, "max_length":300},
		{"name":"targetconf","type":StringAttribute, "max_length":300},
		{"name":"status","type":StringAttribute, "max_length":20},
		{"name":"createdAt","type":DateTimeAttribute, "required":True, "is_nullable": False},
		{"name":"updatedAt","type":DateTimeAttribute}
	]
# ** EndSection ** Entity_NginxOrder
