from temod.storage.mysql import MysqlEntityStorage
from subprocess import Popen, PIPE, STDOUT, check_output
from getpass import getpass
from pathlib import Path
from uuid import uuid4 

import sys
import os

if not os.getcwd() in sys.path:
	sys.path.append(os.getcwd())

from install import common_funcs
from core.entity import *

import mysql.connector
import traceback
import argparse
import toml
import re


APP_VERSION = "1.0.1"


def search_existing_database(credentials):
	try:
		connexion = mysql.connector.connect(**credentials)
	except:
		LOGGER.error("Can't connect to the specified database using these credentials. Verify the credentials and the existence of the database.")
		LOGGER.error(traceback.format_exc())
		sys.exit(1)

	cursor = connexion.cursor()
	cursor.execute('show tables;')

	try:
		return len(cursor.fetchall()) > 0
	except:
		raise
	finally:
		cursor.close()
		connexion.close()


def confirm_database_overwrite():
	print(); common_funcs.print_decorated_title("! DANGER"); print()
	LOGGER.info("The specified database already exists and is not empty. This installation script will erase all the database content and overwrite it with a clean one.")
	rpsn = input("Continue the installation (y/*) ?").lower()
	return rpsn == "y"


def get_admin_infos(username=None, password=None, no_confirm=False):
	print()
	username = os.environ.get('DOCKER_FLASK_MANAGER_ADMIN_USERNAME',username)
	if username is None:
		username = input("Enter the admin username: ")
	password = os.environ.get('DOCKER_FLASK_MANAGER_ADMIN_PASSWORD',password)
	if password is None:
		password = getpass("Enter the admin password: ")

	if not no_confirm:
		print("\n\n"+"*"*20)
		print("Admin Infos: ")
		print(f"username = {username}")
		print(f"password = {password}")
		rspn = input("confirm ? (y/*)").lower()
		if rspn == "y":
			return {"username":username,"password":password}
	else:
		return {"username":username,"password":password}
	return get_admin_infos()


def install_preset_objects(credentials, admin_infos):	
	app = DockerFlaskManager(version=APP_VERSION)
	jobs = [Job(name="DockerComposerJob",state="IDLE")]

	admin_privilege = AccountPrivilege(id=str(uuid4()), label="admin", roles="*")
	admin_user = User(id=str(uuid4()), username=admin_infos['username'], mdp=admin_infos['password'])
	admin_account = UserAccount( id=str(uuid4()), idU=admin_user['id'], idP=admin_privilege['id'])

	MysqlEntityStorage(AccountPrivilege,**credentials).create(admin_privilege)
	MysqlEntityStorage(User,**credentials).create(admin_user)
	MysqlEntityStorage(UserAccount,**credentials).create(admin_account)

	for job in jobs:
		MysqlEntityStorage(Job,**credentials).create(job)
	MysqlEntityStorage(DockerFlaskManager,**credentials).create(app)
	
	return True


def install_dockcoman_service(root_path, virtual_env, logging_dir, services_dir):
	# Install Dockcoman
	with open(os.path.join(root_path,"services","docker_compose_manager","dockcoman.service")) as file:
		service = file.read()
	service = service.replace("$script_path", os.path.join(root_path,"services","docker_compose_manager","dockcoman.sh"))
	if virtual_env is not None:
		service = service.replace("$venv_path", f'-v "{os.path.join(virtual_env,"bin","activate")}"')
	else:
		service = service.replace("$venv_path", "")
	if logging_dir is not None:
		service = service.replace("$logging_dir", f'-l "{logging_dir}"')
	else:
		service = service.replace("$logging_dir", "")
	try:
		with open(os.path.join(services_dir,"dockcoman.service"),"w") as file:
			file.write(service)
		with open(os.path.join(services_dir,"dockcoman.timer"),"w") as file:
			with open(os.path.join(root_path,"services","docker_compose_manager","dockcoman.timer"),"r") as ofile:
				file.write(ofile.read())
	except:
		LOGGER.error(f"Unable to save dockcoman.service file in directory {services_dir}. You can either install the files in another directory with 'install.py -s [DIRECTORY]' or give enough rights to the install script.")
		LOGGER.error("Trace of the exception: ")
		LOGGER.error(traceback.format_exc())
		return False
	return True


def is_nginx_installed():
	try:
		check_output(["nginx","-v"])
		return True
	except:
		pass
	return False


def is_docker_compose_installed():
	try:
		check_output(["docker-compose","--version"])
		return True
	except:
		pass
	return False


def setup(app_paths, args):

	if not is_docker_compose_installed():
		LOGGER.error("docker-compose is not installed on this server. Install it using: apt install docker-compose")
		return False

	if not is_nginx_installed():
		LOGGER.error("Nginx is not installed on this server. Install it using: apt install nginx")
		return False

	credentials = common_funcs.get_mysql_credentials(no_confirm=args.accept_all)
	already_created = search_existing_database(credentials)
	if already_created:
		if not confirm_database_overwrite():
			LOGGER.warning("If you which to just update the app, run the script install/update.py")
			return False

	virtual_env = common_funcs.detect_virtual_env(app_paths['root'])
	logging_dir = args.logging_dir if not args.quiet else None
	if not install_dockcoman_service(app_paths['root'], virtual_env, logging_dir, args.services_dir):
		return False

	admin_infos = get_admin_infos(no_confirm=args.accept_all)

	with open(app_paths['mysql_schema_file']) as file:
		if not common_funcs.execute_mysql_script(credentials, file.read().replace("$database",credentials['database'])):
			return False

	template_config = common_funcs.load_toml_config(app_paths['template_config_file'])
	template_config['storage']['credentials'].update(credentials)
	common_funcs.save_toml_config(template_config, app_paths['config_file'])

	return install_preset_objects(credentials, admin_infos)


if __name__ == "__main__":

	print("\n"); width = common_funcs.print_pattern("Docker Flask Manager"); print(); print("#"*width); print()

	parser = argparse.ArgumentParser(prog="Manages docker through a flask api")
	parser.add_argument(
		'-l', '--logging-dir', 
		help='Directory where log files will be stored', 
		default=os.path.join("/","var","log","docker-flask-manager")
	)
	parser.add_argument(
		'-s', '--services-dir', 
		help='Directory where docker flask manager services files will be stored', 
		default=os.path.join("/","lib","systemd","system")
	)
	parser.add_argument('-y', '--accept-all', action="store_true", help='Equivalent to answer yes to everything', default=False)
	parser.add_argument('-q', '--quiet', action="store_true", help='No logging', default=False)
	args = parser.parse_args()

	setattr(__builtins__,'LOGGER', common_funcs.get_logger(args.logging_dir, quiet=args.quiet))
	app_paths = common_funcs.get_app_paths(Path(os.path.realpath(__file__)).parent)

	if not os.path.isfile(app_paths['mysql_schema_file']):
		LOGGER.error("DB schema file not found at",app_paths['mysql_schema_file'])
		sys.exit(1)

	if not os.path.isfile(app_paths['template_config_file']):
		LOGGER.error("Config template file not found at",app_paths['template_config_file'])
		sys.exit(1)

	if setup(app_paths, args):
		LOGGER.info("Docker Flask Manager setup completed successfully")
	else:
		LOGGER.error("Error while installing Docker Flask Manager")
		exit(1)