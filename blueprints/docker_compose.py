from flask import Blueprint, Response, current_app, request
from flask_login import current_user, login_required

from temod.storage.directory import DirectoryStorage

from tools.JinjaTools import DockerComposerOps
from tools.Docker.dockerd import Dockerd

from jinja2 import Template as JinjaTemplate
from pathlib import Path

import traceback
import docker
import shutil
import json
import yaml
import os


def setup(configuration):
	default = {
		"templates-directory":"resources/docker-composer",
		"containers-directory":"/var/lib/docker-flask-manager"
	}
	docker_compose_blueprint.configuration = {
		key: configuration.get(key, value) for key,value in default.items()
	}
	docker_compose_blueprint.configuration['TemplatesDirectory'] = DirectoryStorage(
		docker_compose_blueprint.configuration['templates-directory'],mode="",createDir=True
	)
	docker_compose_blueprint.configuration['ContainersDirectory'] = DirectoryStorage(
		docker_compose_blueprint.configuration['containers-directory'],mode="",createDir=True
	)
	return docker_compose_blueprint


def get_configuration(config):
	try:
		return docker_compose_blueprint.configuration.get(config)
	except:
		if not hasattr(docker_compose_blueprint,"configuration"):
			setup({})
			return get_configuration(config)
		raise


docker_compose_blueprint = Blueprint('docker_composer', __name__)
docker_compose_blueprint.setup = setup


@docker_compose_blueprint.route('/setup', methods=['POST'])
@login_required
def docker_composer_up():
	body = dict(request.json)

	dockerid = DockerComposition.storage.generate_value('id')
	containers = get_configuration("ContainersDirectory")
	while containers.has(dockerid):
		dockerid = DockerComposition.storage.generate_value('id')

	templates = get_configuration("TemplatesDirectory").subStorage(
		body['image'],createDir=False
	).subStorage(
		body['version'],createDir=False
	)

	default = yaml.safe_load(templates.read("default.yml"))

	config = JinjaTemplate(templates.read("config.yml")).render(GlobalOps=DockerComposerOps, options=body.get('options',{}), default=default)
	config = yaml.safe_load(config)

	compose_file = JinjaTemplate(templates.read("docker-compose.yml")).render(GlobalOps=DockerComposerOps, Dockerd=Dockerd,**config)

	containerDirectory = containers.subStorage(dockerid, createDir=True)
	containerDirectory.write("config.yml",yaml.dump(config))
	containerDirectory.write("docker-compose.yml",compose_file)

	DockerComposition.storage.create(DockerComposition(
		id=dockerid, volumes_path=containerDirectory.directory, name=body['image'], version=body['version']
	))

	if body.get("start-container",True):
		DockerComposeOrder.storage.create(DockerComposeOrder(
			id=DockerComposeOrder.storage.generate_value('id'),
			composition=dockerid,
			cmd="up",
			args="-d"
		))

	data = {"id": dockerid}
	data.update(config)
	return 	Response(response=json.dumps({"status":"ok", "data": data}),status=200)

 	
@docker_compose_blueprint.route('/status/<string:composition>', methods=['GET'])
@login_required
def docker_composer_status(composition):

	composition = DockerComposition.storage.get(id=composition)
	if composition is None:
		return Response(response={"status":"error","error":"composition not found"},status=404)

	containers = DockerCompositionContainer.storage.list(composition=composition['id'])
	stats = {}
	client = docker.DockerClient()
	for container in containers:
		cnt = client.containers.get(container['container'])
		stats[container['container']] = {"status":cnt.status}
	client.close()

	data = {"overview":{"status":all([stat['status'] == "running" for stat in stats.values()])},"containers": stats}
	return 	Response(response=json.dumps({"status":"ok", "data": data}),status=200)





