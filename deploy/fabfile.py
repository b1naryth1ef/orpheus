import getpass

from fabric.contrib.files import upload_template, exists
from fabric.api import *

env.user = getpass.getuser()
env.hosts = ["CsgoEmporiumBackend:43594", "CsgoEmporiumFrontend:43594"]

USERS = {
    "joon": "$6$XJY4rpPg$c1Qa18HYcMlrVASQVyh6Av5Cgm7h7Zm61IixwPtY0o02xeaZKtsAy.jR0Ows/R2isJ5JOEytb5nbUDtRwcQh3.",
    "andrei": "$6$f5O1ho/X$jO8EtochLrThL78rrfxa4ifCkenyoiNlWQUWYetnPR3s3C6ITQaRnIRdCjD6L.v4dgYlZBp7/HwU46uHedQ1S/"
}

def os_user_exists(user):
    if not len(sudo("getent passwd %s" % user)):
        return False
    return True

def os_user_groups(user):
    return run("groups %s" % user).split(" : ", 1)[-1]

def os_create_user(user, password, groups):
    sudo("useradd %s -p %s -m -U" % (user, password))
    for group in groups:
        sudo("adduser %s %s" % (user, group))

def sync_users():
    for user in USERS:
        if not os_user_exists(user):
            os_create_user(user, USERS[user], ["sudo"])
        sync_ssh_keys(user)

def sync_ssh_keys(user):
    if not exists("/home/%s/.ssh" % user):
        sudo("mkdir /home/%s/.ssh" % user)
        sudo("chown %s: /home/%s/.ssh" % (user, user))
    upload_template("keys/%s" % user, "/home/%s/.ssh/authorized_keys" % user, use_jinja=False, backup=False, use_sudo=True)
    sudo('chown %s: /home/%s/.ssh/authorized_keys' % (user, user))

def push_sshd_config():
    upload_template("configs/sshd_config", "/etc/ssh/sshd_config", use_sudo=True)
    sudo("chmod 644 /etc/ssh/sshd_config")
    sudo("chown root: /etc/ssh/sshd_config")

def deploy():
    sync_users()
    push_sshd_config()

