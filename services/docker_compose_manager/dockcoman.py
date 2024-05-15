from temod.base.attribute import DateTimeAttribute
from temod.storage import MysqlEntityStorage
from temod.base.condition import Superior

from datetime import datetime
from pathlib import Path

import subprocess
import traceback
import argparse
import logging
import docker
import toml
import yaml
import sys
import os


DOCKCOMAN_JOB_NAME = "DockerComposerJob"

def load_configs(root_dir):
	with open(os.path.join(root_dir,"config.toml")) as config_file:
		config = toml.load(config_file)
	return config

def get_logger(logging_dir):
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

	if logging_dir is not None and os.path.isdir(logging_dir):
		fh = logging.FileHandler(os.path.join(logging_dir,"dockcoman.log"), 'a')
		fh.setLevel(logging.DEBUG)
		fh.setFormatter(formatter)
		logger.addHandler(fh)
	else:
		print("No valid logging directory specified. No logs will be kept.")

	dh = logging.StreamHandler(sys.stdout)
	dh.setLevel(logging.WARNING)
	dh.setFormatter(formatter)
	logger.addHandler(dh)

	return logger


class DockerComposeOrdersHandler(object):
	"""docstring for DockerComposeOrdersHandler"""
	def __init__(self, **mysql_credentials):
		super(DockerComposeOrdersHandler, self).__init__()
		self.mysql_credentials = mysql_credentials
		self.storages = {
			"dockerContainers": MysqlEntityStorage(entities.DockerContainer,**self.mysql_credentials),
			"dockerCompositions": MysqlEntityStorage(entities.DockerComposition,**self.mysql_credentials),
			"dockerComposeOrders": MysqlEntityStorage(entities.DockerComposeOrder,**self.mysql_credentials),
			"dockerCompositionContainers": MysqlEntityStorage(entities.DockerCompositionContainer,**self.mysql_credentials)
		}


	def handle_order_up(self, order, composition):
		path = composition['volumes_path']
		cwd = os.getcwd()
		os.chdir(path)
		cmd = ["docker-compose",order['cmd']]
		if order['args'] is not None:
			cmd.append(order['args'])
		LOGGER.info(f"Launching docker-compose with cmd {' '.join(cmd)}")
		std_err = ""
		try:
			pipes = subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			std_out, std_err = pipes.communicate()
			LOGGER.info(f"docker-compose cmd returned with exit code : {pipes.returncode}")
			if pipes.returncode != 0:
				LOGGER.error(f"STD ERR: ")
				LOGGER.error(f"{std_err}")
		except:
			LOGGER.error(f"Error executing docker-compose cmd for order {order['id']}")
			LOGGER.error(traceback.format_exc())
			LOGGER.error(f"STD ERR: ")
			LOGGER.error(f"{std_err}")
			return False
		os.chdir(cwd)

		with open(os.path.join(path,"docker-compose.yml")) as file:
			composer_file = yaml.safe_load(file.read())

		client = docker.DockerClient()
		for service, params in composer_file['services'].items():
			container_name = params['container_name']
			LOGGER.info(f"Fetching container by name {container_name}")
			container = client.containers.get(container_name)
			LOGGER.info(f"Container found: {container.id}")
			self.storages['dockerContainers'].create(entities.DockerContainer(
				id=container.id,
				name=container_name,
				image=params['image'],
			))
			self.storages['dockerCompositionContainers'].create(entities.DockerCompositionContainer(
				composition=composition['id'], container=container.id
			))
			LOGGER.info(f"Container {container.id} linked to composition {composition['id']}")
		client.close()
		return True


	def handle_order(self, order):
		composition = self.storages['dockerCompositions'].get(id=order['composition'])
		path = composition['volumes_path']
		if not os.path.isdir(path):
			LOGGER.error(f"Volume path {path} for composition {composition['id']} not found")
			return False

		if order['cmd'] == "up":
			return self.handle_order_up(order, composition)
		LOGGER.error(f"Unknown docker-compose cmd {cmd} for order {order['id']}")
		return False


	def handle(self):
		orders = self.storages['dockerComposeOrders'].list(status=None)

		orders_handled = []
		for order in orders:
			LOGGER.info(f"Handling order {order['id']}")
			order.takeSnapshot()
			result = self.handle_order(order)
			if result:
				order['status'] = "completed"
				LOGGER.info(f"Order {order['id']} handled with success")
			else:
				order['status'] = "failed"
				LOGGER.error(f"Handling order {order['id']} failed")
			order['updatedAt'] = datetime.now()
			self.storages['dockerComposeOrders'].updateOnSnapshot(order)
			orders_handled.append(result)

		if len(orders_handled) == 0:
			LOGGER.info("No orders to handle")
			return None

		return all(orders_handled)
		


class NginxOrdersHandler(object):
	"""docstring for NginxOrdersHandler"""
	def __init__(self, **mysql_credentials):
		super(NginxOrdersHandler, self).__init__()
		self.mysql_credentials = mysql_credentials
		self.nginx_directory = Path("/etc/nginx/sites-enabled")
		self.storages = {
			"nginxOrders": MysqlEntityStorage(entities.NginxOrder,**self.mysql_credentials)
		}

	def handle_order_setup(self,order):
		try:
			target_file = str(self.nginx_directory.joinpath(order['targetconf']))
			base_file = order['baseconf']
			with open(target_file,'w') as file:
				with open(base_file) as base:
					file.write(base.read())
			LOGGER.info(f"Config copied successfully from {base_file} to {target_file}")
			return True
		except:
			LOGGER.error(f"Error while copying Nginx config from {base_file} to {target_file}")
			LOGGER.error(traceback.format_exc())
		return False

	def handle_order(self, order):
		if order['cmd'] == 'setup':
			return self.handle_order_setup(order)
		return True	

	def restart_nginx_service(self):
		try:
			subprocess.check_output(["service","nginx","restart"])
			LOGGER.info(f"Nginx service restarted successfully")
			return True
		except:
			LOGGER.error(f"Error while restarting nginx service")
			LOGGER.error(traceback.format_exc())
		return False


	def handle(self):
		orders = self.storages['nginxOrders'].list(status=None)

		orders_handled = []
		for order in orders:
			LOGGER.info(f"Handling nginx order {order['id']}")
			order.takeSnapshot()
			result = self.handle_order(order)
			if result:
				order['status'] = "completed"
				LOGGER.info(f"Order {order['id']} handled with success")
			else:
				order['status'] = "failed"
				LOGGER.error(f"Handling nginx order {order['id']} failed")
			order['updatedAt'] = datetime.now()
			self.storages['nginxOrders'].updateOnSnapshot(order)
			orders_handled.append(result)

		if len(orders_handled) == 0:
			LOGGER.info("No nginx orders to handle")
			return None

		return self.restart_nginx_service() and all(orders_handled)


def already_running(**mysql_credentials):
	DockcomanJob = MysqlEntityStorage(entities.Job, **mysql_credentials).get(name=DOCKCOMAN_JOB_NAME)
	if DockcomanJob['state'] == "RUNNING":
		return True
	return False

def start_run(**mysql_credentials):
	storage = MysqlEntityStorage(entities.Job, **mysql_credentials)
	DockcomanJob = storage.get(name=DOCKCOMAN_JOB_NAME).takeSnapshot()
	DockcomanJob.setAttribute("state","RUNNING")
	storage.updateOnSnapshot(DockcomanJob)

def stop_run(exit_code, **mysql_credentials):
	storage = MysqlEntityStorage(entities.Job, **mysql_credentials)
	DockcomanJob = storage.get(name=DOCKCOMAN_JOB_NAME).takeSnapshot()
	DockcomanJob.setAttribute("state","IDLE")
	DockcomanJob.setAttribute("last_exit_code",exit_code)
	storage.updateOnSnapshot(DockcomanJob)
	if exit_code != 0:
		sys.exit(exit_code)

def launch(config):
	if already_running(**config["storage"]["credentials"]):
		LOGGER.info("Synchronization is already ongoing. Postponing execution.")
		return
	start_run(**config["storage"]["credentials"])

	handler = DockerComposeOrdersHandler(**config["storage"]["credentials"])
	results = handler.handle()	

	exit_code=0	
	if results is not None:
		if results:
			LOGGER.info("All orders handled successfully.")
		else:
			LOGGER.warning("Some orders did not get handled successfully.")
			exit_code=2

	handler = NginxOrdersHandler(**config["storage"]["credentials"])
	results = handler.handle()	
	if results is not None:
		if results:
			LOGGER.info("All nginx orders handled successfully.")
		else:
			LOGGER.warning("Some nginx orders did not get handled successfully.")
			exit_code=2

	return exit_code

if __name__ == "__main__":
	""" Defining and parsing args """
	parser = argparse.ArgumentParser(prog="Handles docker composer orders")

	parser.add_argument('-r', '--root-dir', help='DigiQuest root directory', default=".")
	parser.add_argument('-l', '--logging-dir', help='Directory where to store logs.', default=None)

	args = parser.parse_args()

	if args.root_dir:
		if not os.path.isdir(args.root_dir):
			print(f"Root directory path must be a valid directory.")
			sys.exit(1)
		if not args.root_dir in sys.path:
			sys.path.append(args.root_dir)
	else:
		sys.exit(1)

	setattr(__builtins__,'LOGGER', get_logger(args.logging_dir))
	
	import core.entity as entities

	config = load_configs(args.root_dir)

	try:
		exit_code = launch(config)
	except:
		LOGGER.error("Dockcoman failed with error. Traceback:")
		LOGGER.error(traceback.format_exc())
		stop_run(1,**config["storage"]["credentials"])
	else:
		stop_run(exit_code,**config["storage"]["credentials"])
