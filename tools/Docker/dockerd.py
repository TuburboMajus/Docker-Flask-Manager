import docker

class Dockerd(object):

	def get_default_bridge():
		client = docker.DockerClient()
		networks = client.networks.list()
		default = None
		for network in networks:
			if network.attrs.get('Options',{}).get("com.docker.network.bridge.default_bridge",False):
				default = network.attrs
				break
		client.close()
		del client
		return default
		