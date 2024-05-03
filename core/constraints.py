from temod.base.constraint import *
from .entity import *


class CSTR_USER_USER_ACCOUNT(EqualityConstraint):
	ATTRIBUTES = [
		{"name":"id","entity":User},
		{"name":"idU","entity":UserAccount},
	]


class CSTR_ACCOUNT_PRIVILEGE_USER_ACCOUNT(EqualityConstraint):
	ATTRIBUTES = [
		{"name":"id","entity":AccountPrivilege},
		{"name":"idP","entity":UserAccount},
	]