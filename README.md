# SCAP_Web

## Deployment Process (Linux Ubuntu 22.04)

### Install Conda System-Wide

Note: If Anaconda is already installed, please skip this step \
\
We use Anaconda as our python package manager. If you prefer, please use a different execution environment management strategy. Instructions will only be included for Anaconda. \
\
From the commandline:
```
sudo apt-get install libgl1-mesa-glx libegl1-mesa libxrandr2 libxrandr2 libxss1 libxcursor1 libxcomposite1 libasound2 libxi6 libxtst6
curl -O https://repo.anaconda.com/archive/Anaconda3-2024.02-1-Linux-x86_64.sh
bash Anaconda3-2024.02-1-Linux-x86_64.sh
```

Please update the Anaconda version based on the most up-to-date release.
When running the bash script, input the following lines separately when asked for license agreement and installation location:
```
yes
/opt/anaconda3
```
  
#### Add conda to your system paths

From the commandline:
```
sudo vi /etc/profile
```

Please insert the following lines at the end of the file:
```
PATH=$PATH:/opt/anaconda3/bin
CONDA_ENVS_PATH=/opt/anaconda3/envs
```

#### Initialize the conda environment

From the commandline:
```
source /etc/profile
source /opt/anaconda3/bin/activate
conda init
```

#### (Optional) Create alias commands for commonly used procedures

From the commandline:
```
sudo vi /etc/profile.d/servir_alias.sh
```

Please insert the following alias commands:
```
alias so='sudo chown -R www-data /servir_apps;  sudo chown -R  root /opt/anaconda3/'
alias uo='sudo chown -R ${USER} /servir_apps; sudo chown -R  ${USER} /opt/anaconda3/'
```

From the commandline:
```
source servir_alias.sh
```

### Install SCAP_Web

Please ensure you have properly configured Github's security measures by following the instructions on [this page](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account?platform=linux).

From the commandline:
```
sudo mkdir /servir_apps
uo						# Alias command was created in previous step
git clone git@github.com:SERVIR/SCAP_Web.git
cd SCAP_Web/
conda env create -f ubuntu_2204.yml
```

### Install PostgreSQL
Note: If preferred, please use a different database manager (changes to the code will be necessary) \
\
TODO

### Install Redis

From the commandline:
```
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
sudo apt-get update
sudo apt-get install redis
```

### Configure SCAP

In your project directory (/servir_apps/SCAP_Web/, if you are following these instructions), create a file named data.json as follows: \
From the terminal:
```
sudo vi /servir_apps/SCAP_Web/data.json
```

Insert the following JSON object, properly replacing the {PLACEHOLDERS} with your unique values (defined at the end of this section):
```
{
  "ALLOWED_HOSTS": [
    "localhost",
    "scap.servirglobal.net",
    "s-cap.servirglobal.net",
    "127.0.0.1"
  ],
  "SECRET_KEY": "{YOUR_SECRET_KEY}",
  "CSRF_TRUSTED_ORIGINS": [
    "https://scap.servirglobal.net",
    "https://s-cap.servirglobal.net",
    "http://127.0.0.1"
  ],
  "ACCOUNT_DEFAULT_HTTP_PROTOCOL": "http",
  "DBUSER": "{YOUR_DB_USER}",
  "USERNAME": "{YOUR_DB_NAME}",
  "PASSWORD": "{YOUR_DB_PASSWORD}",
  "HOST": "{YOUR_DB_IP}",
  "SITE_ID": {SITE_ID},
  "GOOGLE_SECRET_KEY": "{YOUR_GOOGLE_SECRET_KEY}",
  "GOOGLE_CLIENT_ID": "{YOUR_GOOGLE_CLIENT_ID}",
  "SERVICE_ACCOUNT": "{YOUR_GOOGLE_SERVICE_ACCOUNT}",
  "SERVICE_ACCOUNT_JSON": "{YOUR_SERVICE_ACCOUNT_JSON}",
  "PATH_TO_LOG":"s-cap.log",
  "DATA_DIR":"{DATA_DIR}",
  "HTTP_HTTPS": "https",
  "CELERY_BROKER_URL": "{MESSAGE_BROKER_URL}",
  "CELERY_RESULT_BACKEND": "{RESULTS_MESSAGE_BROKER_URL}",
  "UPLOAD_ROOT": "{UPLOAD_ROOT}",
  "MEDIA_URL": "/media/",
  "PROJ_LIB": "/opt/anaconda3/envs/SCAP/share/proj",
  "GDAL_DATA": "/opt/anaconda3/envs/SCAP/share/gdal",
  "EMAIL_HOST": "{EMAIL_HOST}",
  "EMAIL_HOST_USER": "{BOT_EMAIL_ADDRESS}",
  "EMAIL_HOST_PASSWORD": "{BOT_EMAIL_PASSWORD}"
}
```

#### Placeholder definitions and sources
\
You can generate {YOUR_SECRET_KEY} as follows: \
From the commandline:
```
conda activate SCAP
python
```

From the python interpreter:
```
from django.core.management.utils import get_random_secret_key  
get_random_secret_key()
```

##### Celery placeholders:
\
{MESSAGE_BROKER_URL}: Address and port for the message broker Celery should use to execute and manage tasks. If you are deploying according to these instructions, this should be redis://localhost:6379 \
{MESSAGE_BROKER_URL}: Address and port for the message broker Celery should use to store task results. If you are deploying according to these instructions, this should be the same as the task manager; redis://localhost:6379  \

##### PostgreSQL placeholders:
\
{YOUR_DB_USER}: The user that owns the database you created previously, which should be scap_admin if you followed the instructions on this README \
{YOUR_DB_NAME}: The name of the database that holds all the tables for SCAP, which should be scap_db if you followed the instructions on this README \
{YOUR_DB_PASSWORD}: The password for the database owner \
{YOUR_DB_IP}: The IP address of the machine hosting the database; If you are deploying the Django application on the same machine as the PostgreSQL database, this can be localhost or 127.0.0.1. If the machines are on the same network, add the local IP address of the PostgreSQL machine. If they are not on the same network, add the external IP address of the PostgreSQL machine (ensure the machines can talk to each other). \

##### Allauth placeholders:
\
{YOUR_GOOGLE_SECRET_KEY}: \
{YOUR_GOOGLE_CLIENT_ID}: \
{YOUR_GOOGLE_SERVICE_ACCOUNT}: \
{YOUR_SERVICE_ACCOUNT_JSON}: \
{SITE_ID}: This will be replaced at a later step in the instructions

##### Data Directory placeholders:
\
{DATA_DIR}: The location where S-CAP's source files will be stored. Since this folder can grow to contain multiple Terabytes of data, we recommend hosting this data on a mount to a file server. \
{UPLOAD_ROOT}: The location where user files will be uploaded to. This includes images that must be uploaded to populate the various Pilot Country models (scap/models.py > PilotCountry), as well as user uploaded datasets (scap/models.py > ForestCoverFile, AGBCollection, AOICollection) \

##### Email Service placeholders:
\
{EMAIL_HOST}: smtp.gmail.com (if your email bot uses a different email provider, this will differ) \
{BOT_EMAIL_ADDRESS}: Gmail address for your email bot account \
{BOT_EMAIL_PASSWORD}: Password for your email bot account

### Install NGINX

From the commandline:
```
sudo apt update
sudo apt install nginx
```

Create a folder to store NGINX sockets
```
sudo mkdir /servir_apps/socks/
sudo chown www-data /servir_apps/socks/
```

### Set up SSL

From the commandline:
```
sudo mkdir /servir_apps/certs/
sudo chown www-data /servir_apps/certs/           # Move your .key and .pem files into this folder
```

### Create Linux service files

#### Create service file for SCAP

Create the log directory
```
sudo mkdir /var/log/scap/
sudo chown www-data /var/log/scap/
```

From the commandline:
```
sudo vi /etc/systemd/system/scap.service
```

Insert the following configuration for the service file:
```
[Unit]
Description=scap daemon
After=network.target

[Service]
User=www-data
Group=www-data
SocketUser=www-data
WorkingDirectory=/servir_apps/SCAP_Web/
StandardOutput=/var/log/scap/scap_gunicorn.log 
StandardError=/var/log/scap/scap_gunicornerror.log
Environment="GDAL_DATA=/opt/anaconda3/envs/SCAP/share/gdal"
Environment="PROJ_LIB=/opt/anaconda3/envs/SCAP/share/proj"
ExecStart=/opt/anaconda3/envs/SCAP/bin/gunicorn --timeout 700 --workers 32 --pythonpath '/servir_apps/SCAP_Web/,/opt/anaconda3/envs/SCAP/lib/python3.11/site-packages/' --bind unix:/servir_apps/socks/s-cap_prod.sock ScapTestProject.wsgi:application  >> /var/log/scap/scap_gunicorn.log 2>> /var/log/scap/scap_gunicornerror.log

[Install]
WantedBy=multi-user.target
```

From the commandline:
```
sudo systemctl enable scap
```

#### Create service file(s) for Celery

This implementation of SCAP uses multiple queues to process different tasks. That means we need to create Celery workers to handle each queue separately. 

##### Configure Celery directories

Celery needs a location for logging and one for maintaining worker synchronization.
From the commandline:
```
sudo mkdir /var/log/celery/
sudo mkdir /var/run/celery/
sudo chown www-data /var/log/celery/
sudo chown www-data /var/run/celery/
```

When the machine running SCAP reboots, the directories under /var/run/ get deleted. To get around this:
From the commandline:
```
sudo vi /usr/lib/tmpfiles.d/celery.conf
```

Insert the following line:
```
D /var/run/celery 0755 www-data www-data - -
```

Now that we are done configuring the file directories, here are instructions on how to create the service files for one of the workers. The differing configuration settings are mentioned at the end of this section.

From the commandline:
```
sudo vi /etc/systemd/system/celery.service                    # Modify for other celery workers
```

Insert the following configuration for the service file:
```
[Unit]
Description=Celery Service
After=redis-server.service network.target
Requires=redis-server.service
RuntimeDirectory=celery 


[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/etc/conf.d/celery                            # Modify for other celery workers
Environment="GDAL_DATA=/opt/anaconda3/envs/SCAP/share/gdal"
Environment="PROJ_LIB=/opt/anaconda3/envs/SCAP/share/proj"
WorkingDirectory=/servir_apps/SCAP_Web
ExecStart=/bin/bash -c '${CELERY_BIN} -A $CELERY_APP multi start $CELERYD_NODES \
    --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
    --loglevel="${CELERYD_LOG_LEVEL}" $CELERYD_OPTS' 
ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait $CELERYD_NODES \
    --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
    --loglevel="${CELERYD_LOG_LEVEL}"'
ExecReload=/bin/sh -c '${CELERY_BIN} -A $CELERY_APP multi restart $CELERYD_NODES \
    --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
    --loglevel="${CELERYD_LOG_LEVEL}" $CELERYD_OPTS'
Restart=always

[Install]
WantedBy=multi-user.target
```

As seen on the EnvironmentFile line, we specify specific configuration options in an environment file.
From the commandline:
```
sudo vi /etc/conf.d/celery                                   # Modify for other celery workers
```

Insert the following configuration settings:
```
CELERYD_NODES="MainThread"                                   # Modify for other celery workers
DJANGO_SETTINGS_MODULE="ScapTestProject.settings"

# Absolute or relative path to the 'celery' command:
CELERY_BIN="/opt/anaconda3/envs/SCAP/bin/celery"

# App instance to use
CELERY_APP="ScapTestProject"
CELERYD_MULTI="multi"

# Extra command-line arguments to the worker
CELERYD_OPTS="--concurrency=2 --max-tasks-per-child=1"       # Modify for other celery workers
CELERYD_PID_FILE="/var/run/celery/%n.pid"
CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
CELERYD_LOG_LEVEL="INFO"
```

From the commandline:
```
sudo systemctl enable celery
```

Now, create 3 extra service files and their corresponding environment files as follows:

##### File Handler

File: 
/etc/systemd/system/celery_files.service

Modifications: 
```
EnvironmentFile=/etc/conf.d/celery_files
```

Environment File: /etc/conf.d/celery_files
Modifications:
```
CELERYD_NODES="FileHandler"
CELERYD_OPTS="--concurrency=5 --max-tasks-per-child=1 -Q files"
```
Note: The number of concurrent workers that the machine can handle depends on the available resources. Please test and verify that your machine can handle your desired workload. Start small.

From the commandline:
```
sudo systemctl enable celery_files
```

##### Stats Handler

File: 
/etc/systemd/system/celery_stats.service

Modifications: 
```
EnvironmentFile=/etc/conf.d/celery_stats
```

Environment File: /etc/conf.d/celery_stats
Modifications:
```
CELERYD_NODES="StatsHandler"
CELERYD_OPTS="--concurrency=10 --max-tasks-per-child=1 -Q stats"
```
Note: The number of concurrent workers that the machine can handle depends on the available resources. Please test and verify that your machine can handle your desired workload. Start small.

From the commandline:
```
sudo systemctl enable celery_stats
```

##### Synchronization Handler

File: 
/etc/systemd/system/celery_management.service

Modifications: 
```
EnvironmentFile=/etc/conf.d/celery_management
```

Environment File: /etc/conf.d/celery_management
Modifications:
```
CELERYD_NODES="SyncThread"
CELERYD_OPTS="--concurrency=10 --max-tasks-per-child=1 -Q management"
```
Note: The number of concurrent workers that the machine can handle depends on the available resources. Please test and verify that your machine can handle your desired workload. Start small.

From the commandline:
```
sudo systemctl enable celery_management
```

### Create NGINX Configuration Files

From the commandline:
```
sudo vi /etc/nginx/conf.d/s-cap_prod.conf
```

Edit the file with the following configuration:
```
upstream s-cap_prod {
  server unix:/servir_apps/socks/s-cap_prod.sock 
  fail_timeout=0;
}

server {
    listen 443 ssl;
    server_name s-cap.servirglobal.net;
    add_header Access-Control-Allow-Origin *;

    ssl_certificate {PATH TO SSL PEM FILE};                # Replace with your own paths
    ssl_certificate_key {PATH TO SSL KEY FILE};            # Replace with your own paths

    # Some Settings that worked along the way
    client_body_temp_path /tmp;
    client_body_in_file_only on;
    client_body_buffer_size 128K;
    client_max_body_size 20G;
    client_body_timeout 1000;

    proxy_read_timeout 3000;
    proxy_connect_timeout 3000;
    proxy_send_timeout 3000;
    fastcgi_buffers 8 32M;
    fastcgi_buffer_size 128k;
    fastcgi_connect_timeout 180s;
    fastcgi_send_timeout 180s;
    fastcgi_read_timeout 180s;
    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        autoindex on;
        alias /servir_apps/SCAP_Web/static/;
    }

    location /media/ {
        autoindex on;
        alias /servir_apps/SCAP_Web/media/;
    }


    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_pass http://unix:/servir_apps/socks/s-cap_prod.sock ;
    }
}

# Reroute any non https traffic to https
server {
    listen 80;
    server_name s-cap.servirglobal.net;
    rewrite ^(.*) https://$server_name$1 permanent;
}
```

For S-CAP, we create two NGINX configuration files. We must redirect users from scap.servirglobal.net to s-cap.servirglobal.net.

From the commandline:
```
sudo vi /etc/nginx/conf.d/scap_prod.conf
```

Edit the file with the following configuration:
```
upstream scap_prod {
  server unix:/servir_apps/socks/scap_prod.sock 
  fail_timeout=0;
}

server {
  listen 443 ssl;
  server_name scap.servirglobal.net;
  rewrite ^/(.*) https://s-cap.servirglobal.net/$1 permanent;
}

# Reroute any non https traffic to https
server {
    listen 80;
    server_name scap.servirglobal.net;
    rewrite ^(.*) https://s-cap.servirglobal.net/$1 permanent;
}
```
