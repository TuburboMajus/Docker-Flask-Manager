# ** Section ** Imports
from temod.base.condition import *
from temod.base.attribute import *
from temod.base.join import *

from core.entity.user import *
from core.constraints import *
# ** EndSection ** Imports

# ** Section ** Join_AccountFile
class AccountFile(Join):

	DEFAULT_ENTRY = User

	STRUCTURE = [
		CSTR_USER_USER_ACCOUNT(),
		CSTR_ACCOUNT_PRIVILEGE_USER_ACCOUNT()
	]

	EXO_SKELETON = {
		"is_authenticated":"userAccount.is_authenticated",
		"is_active":"userAccount.is_active",
		"username":"user.username",
		"mdp":"user.mdp",
		"id":"userAccount.id",
	}
# ** EndSection ** Join_AccountFile