from flask import Blueprint, Response, current_app, request
from flask_login import current_user, login_required

from temod.base.condition import Equals, Or, In 
from temod.base.attribute import UUID4Attribute

from pathlib import Path

import traceback
import shutil
import json
import os


def setup(configuration):
	default = {}
	login_blueprint.configuration = {
		key: configuration.get(key, value) for key,value in default.items()
	}
	return login_blueprint


def get_configuration(config):
	try:
		return login_blueprint.configuration.get(config)
	except:
		if not hasattr(login_blueprint,"configuration"):
			setup({})
			return get_configuration(config)
		raise


login_blueprint = Blueprint('login', __name__)
login_blueprint.setup = setup


@login_blueprint.route('/login', methods=["GET",'POST'])
def login():
	user = AUTHENTICATOR.search_user(request.form.get("username"),request.form.get("password"))
	if user is not None:
		AUTHENTICATOR.login_user(user)
		return Response(json.dumps(
			{"token": user['token'], "tokenExpiration": user['expiration_date'], "error": None}
		), status=200, mimetype='application/json')
	return Response(json.dumps({"error": "Unknown user"}), status=403, mimetype='application/json')

@login_blueprint.route('/logout',methods=['GET'])
@login_required
def logout():
	session.clear()
	AUTHENTICATOR.logout_user(current_user)
	return Response(json.dumps({"disconnected":"ok"}), status=200, mimetype='application/json')