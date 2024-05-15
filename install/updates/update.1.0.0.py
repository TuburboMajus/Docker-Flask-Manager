from subprocess import check_output
from datetime import datetime

MYSQL_CMD = f"""
ALTER TABLE dockerComposeOrder ADD createdAt datetime not null default "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}";
ALTER TABLE dockerComposeOrder ADD updatedAt datetime;

create table nginxOrder(
    id varchar(36) primary key not null,
    cmd varchar(50) not null,
    baseconf varchar(300),
    targetconf varchar(300),
    status varchar(20),
    createdAt datetime not null,
    updatedAt datetime
);

UPDATE dockerFlaskManager SET version = "1.0.1";
"""


def is_nginx_installed():
	try:
		check_output(["nginx","-v"])
		return True
	except:
		pass
	return False


def launch_update(common_funcs, app_paths, app_config, mysql_credentials=None, **kwargs):
	if not is_nginx_installed():
		LOGGER.error("Nginx is not installed on this server. Install it using: apt install nginx")
		return False

	return common_funcs.execute_mysql_script(mysql_credentials, MYSQL_CMD)