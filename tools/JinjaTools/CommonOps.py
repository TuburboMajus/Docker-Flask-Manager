import socket
	
UNUSED_PORTS_RANGE = [3500, 65000]

def get_unused_port(exclude=None, ignore_range=False):
	port = None
	excluded = [] if exclude is None else ([exclude] if type(exclude) is int else exclude)
	while port is None:
		sock = socket.socket()
		sock.bind(('', 0))
		port = int(sock.getsockname()[1])
		if port in excluded:
			port = None
		elif (port < UNUSED_PORTS_RANGE[0] or port > UNUSED_PORTS_RANGE[1]) and not ignore_range:
			port = None
		sock.close()
		del sock
	return port