from flask import Blueprint, Response, current_app, request
from flask_login import current_user, login_required

from temod.storage.directory import DirectoryStorage

from tools.JinjaTools import DockerComposerOps
from tools.Docker.dockerd import Dockerd

from jinja2 import Template as JinjaTemplate
from datetime import datetime
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


@docker_compose_blueprint.route('/create', methods=['POST'])
@login_required
def docker_composer_new():
	body = dict(request.json)

	templates = get_configuration("TemplatesDirectory").subStorage(
		body['image'],createDir=True
	).subStorage(
		body['version'],createDir=True
	)

	for filename, file in body['files'].items():
		templates.write(filename, file)

	return 	Response(response=json.dumps({"status":"ok"}),status=200)


@docker_compose_blueprint.route('/check/<string:composition>/<string:version>', methods=['GET'])
@login_required
def docker_composer_check(composition, version):

	templates = get_configuration("TemplatesDirectory").subStorage(
		composition,createDir=False
	).subStorage(
		version,createDir=False
	)

	data = {"files":{}, "errors":[]}
	for file in ['default.yml','config.yml','docker-compose.yml']:
		data['files'][file] = templates.has(file) 

	return 	Response(response=json.dumps({"status":"ok", "data":data}),status=200)


@docker_compose_blueprint.route('/setup', methods=['POST'])
@login_required
def docker_composer_up():
	body = dict(request.json)
	warnings = []

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

	config = JinjaTemplate(templates.read("config.yml")).render(
		GlobalOps=DockerComposerOps, options=body.get('options',{}), default=default
	)
	config = yaml.safe_load(config)

	containerDirectory = containers.subStorage(dockerid, createDir=True)
	containerDirectory.write("config.yml",yaml.dump(config))

	for file in templates.content(only_files=True):
		if not file.endswith(".template"):
			continue
		file_content = JinjaTemplate(templates.read(file)).render(GlobalOps=DockerComposerOps, Dockerd=Dockerd,**config)
		containerDirectory.write('.'.join(file.split('.')[:-1]),file_content)

	DockerComposition.storage.create(DockerComposition(
		id=dockerid, volumes_path=containerDirectory.directory, name=body['image'], version=body['version']
	))

	if body.get("start-container",True):
		DockerComposeOrder.storage.create(DockerComposeOrder(
			id=DockerComposeOrder.storage.generate_value('id'),
			composition=dockerid,
			cmd="up",
			args="-d",
			createdAt=datetime.now()
		))

	if body.get("setup-nginx",True):
		if containerDirectory.has("nginx_config"):
			NginxOrder.storage.create(NginxOrder(
				id=NginxOrder.storage.generate_value('id'),
				cmd="setup",
				baseconf=str(Path(containerDirectory.directory).joinpath("nginx_config")),
				targetconf=dockerid,
				createdAt=datetime.now()
			))
		else:
			warnings.append("setup-nginx is set to True but no nginx_config file found")

	data = {"id": dockerid}
	data.update({"config":config})
	if len(warnings) > 0:
		data.update({"warnings":warnings})
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





