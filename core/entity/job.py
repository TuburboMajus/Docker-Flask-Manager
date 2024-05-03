# ** Section ** Imports
from temod.base.entity import Entity
from temod.base.attribute import *
from copy import deepcopy
# ** EndSection ** Imports


# ** Section ** Entity_Job
class Job(Entity):
	ENTITY_NAME = "job"
	ATTRIBUTES = [
		{"name":"name","type":StringAttribute,"max_length":50, "required":True,"is_id":True,"is_nullable":False},
		{"name":"state","type":StringAttribute,"max_length":20, "is_nullable":False, "default_value": "IDLE"},
		{"name":"last_exit_code","type":IntegerAttribute}
	]
# ** EndSection ** Entity_Job