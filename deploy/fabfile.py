import getpass, os, re, uuid

from fabric.contrib.files import upload_template, exists
from fabric.api import *
from fabric.colors import *

from data import USERS, REPOS, BASE_PACKAGES, ROLE_PACKAGES

env.servers = {
    "cdn": ["eapp01.csgoemporium.com", "eapp02.csgoemporium.com"],
    "app": ["mona"]
}

env.port = 43594
env.hosts = []
env.user = getpass.getuser()
env.forward_agent = True

env.to_change = {}

def sync_file(localf, remote, owner="emporium", mode="600", refresh=[], context={}, exe=False, jinja=False):
    tmp_name = "/tmp/%s.tmp" % uuid.uuid4()

    if jinja:
        upload_template(localf, tmp_name, use_jinja=jinja, use_sudo=True, backup=False, context=context)

    # TODO: check mode/owner
    if exists(remote):
        org_md5 = sudo("md5sum %s" % remote, quiet=True).split(" ")[0]

        if jinja:
            new_md5 = sudo("md5sum %s" % tmp_name).split(" ")[0]
        else:
            new_md5 = local("md5sum %s" % localf, capture=True).split(" ")[0]

        if org_md5 != new_md5:
            if not jinja:
                upload_template(localf, tmp_name, use_jinja=jinja, use_sudo=True, backup=False, context=context)

            print cyan("File `%s` changed (%s vs %s)..." % (remote, org_md5, new_md5))
            if 'ASCII' in run("file %s" % tmp_name):
                sudo("diff -u --ignore-all-space %s %s | colordiff" % (remote, tmp_name))
        else:
                return
    elif not jinja:
        upload_template(localf, tmp_name, use_jinja=jinja, use_sudo=True, backup=False, context=context)

    for command in refresh:
        print red("  Would trigger refresh: %s" % command)

    env.to_change[env.host_string][tmp_name] = {
        "dest": remote,
        "owner": owner,
        "mode": mode,
        "refresh": refresh,
        "exec": exe
    }

def deploy_redis():
    sync_file("configs/redis/app.conf", "/etc/redis/redis.conf", owner="root", mode="644", refresh=[
        "service redis-server restart"
    ])

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
    upload_template("configs/apt/pgdg.list", "/etc/apt/sources.list.d/pgdg.list", use_sudo=True, backup=False)

    sudo("apt-get update", quiet=True)
    ensure_installed("postgresql-9.4", "postgresql-client-9.4", "postgresql-common", "postgresql-server-dev-9.4")

    upload_template("configs/postgres/postgresql.conf", "/etc/postgresql/9.4/main/postgresql.conf", use_sudo=True, backup=False)
    upload_template("configs/postgres/pg_hba.conf", "/etc/postgresql/9.4/main/pg_hba.conf", use_sudo=True, backup=False)
    sudo("chown -R postgres: /etc/postgresql/9.4/main/")
    sudo("service postgresql restart")

    pg_users = {k: v["pg"] for (k, v) in USERS.iteritems() if v["pg"]}
    upload_template("configs/postgres/bootstrap.sql", "/tmp/bootstrap.sql", use_sudo=True, context={
        "users": pg_users,
    }, use_jinja=True, backup=False)

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
    upload_template("keys/%s" % user, "/home/%s/.ssh/authorized_keys" % user,
            use_jinja=False, backup=False, use_sudo=True)
    sudo('chown %s: /home/%s/.ssh/authorized_keys' % (user, user))

def setup_sshd():
    upload_template("configs/sshd_config", "/etc/ssh/sshd_config", use_sudo=True, backup=False)
    sudo("chmod 644 /etc/ssh/sshd_config")
    sudo("chown root: /etc/ssh/sshd_config")
    sudo("service ssh restart", warn_only=True)

def deploy_pgbouncer():
    sync_file("configs/postgres/pgbouncer.ini",
        "/etc/pgbouncer/pgbouncer.ini", owner="emporium", mode="600",
        refresh=["supervisorctl restart pgbouncer"])

def deploy_supervisor():
    for template in os.listdir("configs/supervisor/"):
        sync_file("configs/supervisor/%s" % template, "/etc/supervisor/conf.d/%s" % template, refresh=[
            "supervisorctl reread",
            "supervisorctl update"
        ])

def deploy_app_nginx():
    sync_file("configs/nginx/emporium", "/etc/nginx/sites-enabled/emporium", refresh=[
        "service nginx reload"
    ])

def deploy_cdn_nginx():
    sync_file("configs/nginx/cdn", "/etc/nginx/sites-enabled/cdn", refresh=[
        "service nginx reload"
    ])

def sync_repos():
    refresh = False

    if not exists('/var/www'):
        sudo("mkdir /var/www")
        sudo("chown emporium: /var/www")

    if not exists("/var/repos"):
        sudo("mkdir /var/repos")
        sudo("chmod 777 /var/repos")

    if exists("/tmp/clone"):
        # TODO: this could fuck us?
        sudo("rm -rf /tmp/clone")

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
                sudo("chmod -R 777 .")
                v = run("git rev-parse HEAD").strip()
                run("git reset --hard origin/master")
                run("git pull origin master")
                sudo("chown -R emporium: .")
                # sudo("chown -R www-data: app/static/")
                if v != run("git rev-parse HEAD").strip():
                    refresh = True

    if refresh:
        # TODO
        print "Would restart shit..."

# TODO: venv
def sync_requirements():
    sudo("pip install -r /var/www/emporium/app/requirements.txt")

def sync_paths():
    if not exists("/var/run/emporium"):
        sudo("mkdir /var/run/emporium")
        sudo("chown emporium: /var/run/emporium")
        sudo("chmod 744 /var/run/emporium")

    if not exists("/var/log/emporium"):
        sudo("mkdir /var/log/emporium")
        sudo("chown emporium: /var/log/emporium")
        sudo("chmod 744 /var/log/emporium")

def deploy_uwsgi():
    sync_file("configs/uwsgi/emporium.json", "/etc/emporium.json", context={"env": "PROD"},
        mode="644", owner="emporium", jinja=True)
    sync_file("configs/uwsgi/uwsgi.bin", "/var/www/emporium/uwsgi.bin", mode="644", owner="emporium",
        exe=True)

def refresh_uwsgi():
    sudo("kill -SIGHUP $(cat /var/run/emporium/uwsgi.pid)")

def checkout_sha(sha):
    with cd("/var/www/emporium"):
        run("git checkout %s" % sha)

def code(sha=None):
    sync_repos()
    if sha:
        checkout_sha(sha)
    refresh_uwsgi()

def deploy():
    env.to_change[env.host_string] = {}
    if env.role in ["app", "cdn"]:
        deploy_cdn()

    if env.role in ["app"]:
        deploy_app()

def build_js():
    with cd("/var/www/emporium/app"):
        sudo("./run js")

def deploy_cdn():
    print green("Deploying CDN Server: %s" % env.host)

    sync_repos()
    build_js()

    deploy_cdn_nginx()
    print cyan("  %s to be applied" % len(env.to_change[env.host_string]))

def deploy_app():
    """
    A full deploy makes sure all configs are up-to-snuff
    """
    print green("Deploying App Server: %s" % env.host)

    # Deploy pgbouncer
    deploy_pgbouncer()

    # Deploy redis
    deploy_redis()

    # Sync secret file
    sync_file("configs/secret.json", "/etc/secret.json", owner="emporium", mode="600")

    # Python stuff
    sync_repos()
    sync_requirements()

    # Sync rush binary
    sync_file("binaries/rush", "/var/www/emporium/rush", owner='emporium', mode='744')

    deploy_supervisor()
    deploy_uwsgi()
    deploy_app_nginx()

    print cyan("  %s to be applied" % len(env.to_change[env.host_string]))

def bootstrap():
    env.user = "root"
    env.port = 22

    print blue("Updating apt...")
    run("apt-get update")
    run("apt-get install sudo")

    print blue("Setting up packages...")
    ensure_installed(*(BASE_PACKAGES + ROLE_PACKAGES[env.role]))

    print blue("Correcting pip installation...")
    sudo("easy_install -U pip")

    print blue("Setting up users...")
    setup_users()

    print blue("Setting up sshd...")
    setup_sshd()

    print blue("Setting up UFW...")
    setup_ufw()

    print blue("Setting up Redis...")
    setup_redis()

    print blue("Setting up look and feel...")
    setup_looknfeel()

    if env.role == "db":
        print "Setting up postgres..."
        setup_postgres()

    if env.role == "app":
        print "Setting up PGBouncer..."
        setup_pgbouncer()

        print "Deploying initial code..."
        sync_paths()
        deploy()

def apply():
    refreshes = set()

    for src, info in env.to_change[env.host_string].items():
        sudo("mv %s %s" % (src, info['dest']))

        if 'owner' in info:
            sudo("chown %s: %s" % (info['owner'], info['dest']))

        if 'mode' in info:
            sudo("chmod %s %s" % (info['mode'], info['dest']))

        if info.get('exec'):
            sudo("chmod +x %s" % info['dst'])

        if info.get('refresh'):
            for command in info.get('refresh'):
                refreshes.add(command)

    print red("Refreshing %s services..." % (len(refreshes), ))
    map(sudo, refreshes)

def cdn():
    env.hosts = env.servers["cdn"]
    env.role = "cdn"

def mona():
    env.hosts = ['mona.hydr0.com']
    env.port = 50000
    env.role = "app"
    env.num = "0"

def hosts(hosts):
    env.hosts = hosts.split(",")

def user(user):
    env.user = user

