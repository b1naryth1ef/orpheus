import getpass, os

from fabric.contrib.files import upload_template, exists
from fabric.api import *

env.user = getpass.getuser()
env.hosts = ['192.210.231.127:43594']
env.forward_agent = True

USERS = {
    "joon": {
        "unix": "$6$XJY4rpPg$c1Qa18HYcMlrVASQVyh6Av5Cgm7h7Zm61IixwPtY0o02xeaZKtsAy.jR0Ows/R2isJ5JOEytb5nbUDtRwcQh3.",
        "pg": None
    },
    "andrei": {
        "unix": "$6$f5O1ho/X$jO8EtochLrThL78rrfxa4ifCkenyoiNlWQUWYetnPR3s3C6ITQaRnIRdCjD6L.v4dgYlZBp7/HwU46uHedQ1S/",
        "pg": "$1$nM.E5Wx1$Us3v2tPJUS2oqwQ270aeP."
    },
    "emporium": {
        "unix": None,
        "pg": None
    }
}

REPOS = {
    "git@github.com:parkjoon/csgoemporiumfrontend.git": ("frontend", "/var/www/emporium")
}

PACKAGES = [
    "htop", "vim-nox", "tmux", "python2.7", "python2.7-dev",
    "python-pip", "screen", "redis-server", "nginx", "git",
    "ufw", "libffi-dev", "libxml2", "libxslt1-dev"
]

def setup_postgres():
    sudo("wget -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | apt-key add -")
    upload_template("configs/apt/pgdg.list", "/etc/apt/sources.list.d/pgdg.list", use_sudo=True)

    sudo("apt-get update", quiet=True)
    ensure_installed("postgresql-9.4", "postgresql-client-9.4", "postgresql-common", "postgresql-server-dev-9.4")

    upload_template("configs/postgres/pg_hba.conf", "/etc/postgresql/9.4/main/pg_hba.conf", use_sudo=True)
    sudo("chown postgres: /etc/postgresql/9.4/main/pg_hba.conf")

    pg_users = {k: v["pg"] for (k, v) in USERS.iteritems() if v["pg"]}
    upload_template("configs/postgres/bootstrap.sql", "/tmp/bootstrap.sql", use_sudo=True, context={
        "users": pg_users,
        "password": "md5$1$XGM08BDs$2sq6zAMzlZiP5VwKXgruH."
    }, use_jinja=True)

    sudo('su postgres -c "psql -a -f /tmp/bootstrap.sql"')
    sudo("shred -n 200 /tmp/bootstrap.sql")
    sudo("rm -rf /tmp/bootstrap.sql")

def ensure_installed(*packages):
    need = []
    for pkg in packages:
        if run("dpkg -s %s" % pkg, quiet=True).return_code == 0:
            continue
        else:
            need.append(pkg)

    if len(need):
        sudo("apt-get install --yes %s" % ' '.join(need))

def os_user_exists(user):
    with warn_only():
        if not len(sudo("getent passwd %s" % user)):
            return False
        return True

def os_user_groups(user):
    return run("groups %s" % user).split(" : ", 1)[-1]

def os_create_user(user, password, groups):
    args = ["-m", "-U"]

    if password:
        args.append("-p '%s'" % password)

    sudo("useradd %s %s" % (user, ' '.join(args)))
    for group in groups:
        sudo("adduser %s %s" % (user, group))

def sync_users():
    for user in USERS:
        if not os_user_exists(user):
            os_create_user(user, USERS[user]["unix"], ["sudo"])
        sync_ssh_keys(user)

def sync_ssh_keys(user):
    if not os.path.exists("keys/%s" % user):
        return
    if not exists("/home/%s/.ssh" % user):
        sudo("mkdir /home/%s/.ssh" % user)
        sudo("chown %s: /home/%s/.ssh" % (user, user))
    upload_template("keys/%s" % user, "/home/%s/.ssh/authorized_keys" % user, use_jinja=False, backup=False, use_sudo=True)
    sudo('chown %s: /home/%s/.ssh/authorized_keys' % (user, user))

def push_sshd_config():
    upload_template("configs/sshd_config", "/etc/ssh/sshd_config", use_sudo=True)
    sudo("chmod 644 /etc/ssh/sshd_config")
    sudo("chown root: /etc/ssh/sshd_config")
    sudo("service ssh restart", warn_only=True)

def setup_supervisor():
    ensure_installed("supervisor")

    for template in os.listdir("configs/supervisor/"):
        upload_template("configs/supervisor/%s" % template, "/etc/supervisor/conf.d/%s" % template, use_sudo=True)

    sudo("service supervisor start", warn_only=True)
    sudo("supervisorctl reread")
    sudo("supervisorctl update")

def sync_repos():
    refresh = False

    if not exists("/var/repos"):
        sudo("mkdir /var/repos")
        sudo("chmod 777 /var/repos")

    for repo, etc in REPOS.items():
        name, diro = etc
        if not exists(diro):
            run("git clone %s /tmp/clone" % repo)
            sudo("mv /tmp/clone %s" % diro)
            sudo("chmod -R 777 %s" % diro)
            sudo("chown -R emporium: %s" % diro)
            refresh = True
        else:
            with cd(diro):
                v = run("git rev-parse HEAD").strip()
                run("git reset --hard origin/master")
                run("git pull origin master")
                sudo("chown -R www-data: app/static/")
                if v != run("git rev-parse HEAD").strip():
                    refresh = True

    if refresh:
        # TODO
        print "Would restart shit..."

def sync_requirements():
    sudo("pip install -r /var/www/emporium/app/requirements.txt")

def sync_rush():
    remote_md5 = run("md5sum /var/www/emporium/rush").split(" ")[0]
    local_md5 = local("md5sum binaries/rush", capture=True).split(" ")[0]

    if remote_md5 == local_md5:
        print "Rush binary matches, not uploading..."
        return

    put("binaries/rush", remote_path="/var/www/emporium/rush", use_sudo=True)
    sudo("chmod 744 /var/www/emporium/rush")
    sudo("chown emporium: /var/www/emporium/rush")

def deploy():
    sync_repos()
    sync_requirements()
    sync_rush()
    setup_supervisor()

def host(host):
    env.hosts = [host]

def bootstrap():
    env.user = "root"

    print "Updating apt..."
    sudo("apt-get update", quiet=True)

    print "Nuking bad packages..."
    sudo("apt-get purge --yes apache2", quiet=True)

    print "Setting up packages..."
    ensure_installed(*PACKAGES)

    print "Setting up postgres..."
    setup_postgres()

    print "Syncing users..."
    sync_users()

    print "Setting up sshd..."
    push_sshd_config()

    print "Deploying initial code..."
    deploy()
