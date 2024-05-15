from temod.storage.mysql import MysqlEntityStorage
from packaging import version
from pathlib import Path

import sys
import os

if not os.getcwd() in sys.path:
	sys.path.append(os.getcwd())

from install import common_funcs
from core.entity import *

import importlib.machinery
import mysql.connector
import traceback
import argparse
import logging


ALL_VERSIONS = ["1.0.0","1.0.1"]


def detected_installed_version(credentials):	
	dockerFlaskManager = list(MysqlEntityStorage(DockerFlaskManager,**credentials).list())[0]
	return dockerFlaskManager['version']


def update_from_version(version, app_paths, app_config, mysql_credentials, args):
	script = os.path.join(app_paths["updates"],f"update.{version}.py")
	if not os.path.isfile(script):
		LOGGER.error(f"Update script from version {version} not found.")
		return

	loader = importlib.machinery.SourceFileLoader(f'upd_{version.replace(".","_")}', script)
	mod = loader.load_module()

	return mod.launch_update(common_funcs, app_paths, app_config, mysql_credentials=mysql_credentials, script_args=args)


def update(app_paths):
	config = common_funcs.load_toml_config(app_paths['config_file'])
	try:
		mysql_credentials = config['storage']['credentials']
		LOGGER.info("Mysql database credentials were detected from your Docker Flask Manager installation.")
	except:
		LOGGER.warning("Couldn't read Mysql credentials from configs file")
		mysql_credentials = {}

	mysql_credentials = common_funcs.get_mysql_credentials(**mysql_credentials)

	all_versions = sorted(ALL_VERSIONS, key=lambda x:version.parse(x))
	latest_version = all_versions[-1]
	ovrld_version = detected_installed_version(mysql_credentials)
	if ovrld_version == latest_version:
		LOGGER.info(f"DockerFlaskManager is already at the lastest version {ovrld_version}")
		return True

	LOGGER.info(f"DockerFlaskManager installed version detected: {ovrld_version}")
	rspn = input(f"Update to latest version {latest_version} ? (y/*)").lower()
	to_version = latest_version
	if rspn != "y":
		rspn = input("Update to a specific version ? (y/*)").lower()
		if rspn != "y":
			LOGGER.info("Exiting update script.")
			sys.exit()
		to_version = input("To which version do you want to update ?")

	if not to_version in all_versions:
		LOGGER.error(f"Version {version} not found. Available versions are {', '.join(all_versions)}.")
		return False

	final_config = common_funcs.load_toml_config(app_paths['template_config_file'])
	while ovrld_version != to_version:

		if not update_from_version(ovrld_version, app_paths, common_funcs.merge_configs(final_config, config), mysql_credentials, args):
			LOGGER.error(f"Update from version {ovrld_version} failed.")
			return False

		new_version = detected_installed_version(mysql_credentials)
		if new_version == ovrld_version:
			LOGGER.error(f"Update from version {ovrld_version} most likely failed. Detected version hasn't changed.")
			return False

		LOGGER.info(f"Version updated succesfully from {ovrld_version} to {new_version}")
		ovrld_version = new_version

	common_funcs.save_toml_config(final_config, app_paths['config_file'])
	return True


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
	parser.add_argument('-q', '--quiet', action="store_true", help='No logging', default=False)
	args = parser.parse_args()

	setattr(__builtins__,'LOGGER', common_funcs.get_logger(args.logging_dir, quiet=args.quiet))
	app_paths = common_funcs.get_app_paths(Path(os.path.realpath(__file__)).parent)

	if not os.path.isdir(app_paths['updates']):
		LOGGER.error("Updates scripts not found at ",updates_dir)
		sys.exit(1)

	if update(app_paths):
		LOGGER.info("Update successfully completed.")
	else:
		LOGGER.error("Update terminated with an error.")
		sys.exit(1)

