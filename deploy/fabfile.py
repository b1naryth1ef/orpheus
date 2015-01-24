import getpass, os, re

from fabric.contrib.files import upload_template, exists
from fabric.api import *
from fabric.colors import *

from data import USERS, REPOS, BASE_PACKAGES, ROLE_PACKAGES

env.servers = {
    "db": ["edb01"],
    "app": ["eapp01"]
}

env.hosts = []
env.user = getpass.getuser()
env.forward_agent = True

def parse_hostname(name):
    return re.findall("e([a-zA-Z]+)([0-9]+)", name)[0]

def setup_ufw():
    sudo("ufw default deny incoming")
    sudo("ufw default allow outgoing")

    # SSH
    sudo("ufw allow 43594/tcp")

    if env.role == "app":
        # HTTP/HTTPS
        sudo("ufw allow 80/tcp")
        sudo("ufw allow 443/tcp")

    sudo("ufw enable")

def setup_postgres():
    sudo("wget -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | apt-key add -")
    upload_template("configs/apt/pgdg.list", "/etc/apt/sources.list.d/pgdg.list", use_sudo=True)

    sudo("apt-get update", quiet=True)
    ensure_installed("postgresql-9.4", "postgresql-client-9.4", "postgresql-common", "postgresql-server-dev-9.4")

    upload_template("configs/postgres/postgresql.conf", "/etc/postgresql/9.4/main/postgresql.conf", use_sudo=True)
    upload_template("configs/postgres/pg_hba.conf", "/etc/postgresql/9.4/main/pg_hba.conf", use_sudo=True)
    sudo("chown -R postgres: /etc/postgresql/9.4/main/")
    sudo("service postgresql restart")

    pg_users = {k: v["pg"] for (k, v) in USERS.iteritems() if v["pg"]}
    upload_template("configs/postgres/bootstrap.sql", "/tmp/bootstrap.sql", use_sudo=True, context={
        "users": pg_users,
    }, use_jinja=True)

    sudo('su postgres -c "psql -a -f /tmp/bootstrap.sql"')
    sudo("shred -n 200 /tmp/bootstrap.sql")
    sudo("rm -rf /tmp/bootstrap.sql")

def setup_looknfeel():
    # Set the hostname
    sudo("hostname %s" % env.host)
    sudo("sed -i 's/127.0.1.1.*/127.0.1.1\t'\"%s\"'/g' /etc/hosts" % env.host)

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

def setup_users():
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

def setup_sshd():
    upload_template("configs/sshd_config", "/etc/ssh/sshd_config", use_sudo=True)
    sudo("chmod 644 /etc/ssh/sshd_config")
    sudo("chown root: /etc/ssh/sshd_config")
    sudo("service ssh restart", warn_only=True)

def sync_supervisor():
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
    env.role, env.num = parse_hostname(env.host)
    if env.role not in ["app"]:
        print red("ERROR: Cannot deploy to server with role %s!" % role)
        return

    sync_repos()
    sync_requirements()
    sync_rush()
    sync_supervisor()

def bootstrap():
    env.role, env.num = parse_hostname(env.host)
    env.user = "root"

    print blue("Updating apt...")
    sudo("apt-get update", quiet=True)

    print blue("Nuking bad packages...")
    sudo("apt-get purge --yes apache2", quiet=True)

    print blue("Setting up packages...")
    ensure_installed(BASE_PACKAGES + ROLE_PACKAGES[env.role])

    print blue("Setting up users...")
    setup_users()

    print blue("Setting up sshd...")
    setup_sshd()

    print blue("Setting up UFW...")
    setup_ufw()

    print blue("Setting up look and feel...")
    setup_looknfeel()

    if env.role == "db":
        print "Setting up postgres..."
        setup_postgres()

    if env.role == "app":
        print "Deploying initial code..."
        deploy()

def db():
    env.hosts = env.servers['db']

def app():
    env.hosts = env.servers['app']

