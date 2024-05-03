# ** Section ** Imports
from temod.base.entity import Entity
from temod.base.attribute import *
from copy import deepcopy
# ** EndSection ** Imports


# ** Section ** Entity_User
class User(Entity):
	ENTITY_NAME = "user"
	ATTRIBUTES = [
		{"name":"id","type":UUID4Attribute,"required":True,"is_id":True,"non_empty":True,"is_nullable":False},
		{"name":"username","type":UTF8BASE64Attribute,"required":True,"non_empty":True,"force_lower_case":True,"is_nullable":False},
		{"name":"mdp","type":UTF8BASE64Attribute,"required":True,"non_empty":True,"is_nullable":False},
		{"name":"token","type":UUID4Attribute,"required":False,"is_nullable":True},
		{"name":"expiration_date","type":DateTimeAttribute,"required":False,"is_nullable":True}
	]
# ** EndSection ** Entity_User


# ** Section ** Entity_UserAccount
class UserAccount(Entity):
	ENTITY_NAME = "userAccount"
	ATTRIBUTES = [
		{"name":"id","type":UUID4Attribute,"required":True,"is_id":True,"non_empty":True,"is_nullable":False},
		{"name":"idU","type":UUID4Attribute,"required":True,"non_empty":True,"is_nullable":False},
		{"name":"idP","type":UUID4Attribute,"non_empty":True,"is_nullable":False},
		{"name":"is_authenticated","type":BooleanAttribute,"is_nullable":False,"default_value":False},
		{"name":"is_active","type":BooleanAttribute,"is_nullable":False,"default_value":False},
		{"name":"is_disabled","type":BooleanAttribute,"is_nullable":False,"default_value":False},
		{"name":"language","type":StringAttribute,"non_empty":True,"is_nullable":False,"default_value":"fr"}
	]
	
	def get_id(self):
		return self.id
# ** EndSection ** Entity_UserAccount


# ** Section ** Entity_AccountPrivilege
class AccountPrivilege(Entity):
	ENTITY_NAME = "accountPrivilege"
	ATTRIBUTES = [
		{"name":"id","type":UUID4Attribute,"required":True,"is_id":True,"non_empty":True,"is_nullable":False},
		{"name":"label","type":StringAttribute,"required":True,"non_empty":True,"is_nullable":False},
		{"name":"roles","type":StringAttribute,"required":True,"non_empty":True,"is_nullable":False}
	]
# ** EndSection ** Entity_AccountPrivilege