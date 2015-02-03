USERS = {
    "joon": {
        "unix": "$6$XJY4rpPg$c1Qa18HYcMlrVASQVyh6Av5Cgm7h7Zm61IixwPtY0o02xeaZKtsAy.jR0Ows/R2isJ5JOEytb5nbUDtRwcQh3.",
        "pg": None
    },
    "andrei": {
        "unix": "$6$f5O1ho/X$jO8EtochLrThL78rrfxa4ifCkenyoiNlWQUWYetnPR3s3C6ITQaRnIRdCjD6L.v4dgYlZBp7/HwU46uHedQ1S/",
        "pg": "1b0daf8de16ebfe51d1f93f90db82b03"
    },
    "emporium": {
        "unix": None,
        "pg": "ef8506a7d156e0cef6f1b6be663c80c6"
    }
}

REPOS = {
    "git@github.com:parkjoon/csgoemporiumfrontend.git": ("frontend", "/var/www/emporium")
}

BASE_PACKAGES = [
    "htop", "vim-nox", "iotop", "iftop", "iotop", "nethogs",
    "screen", "git", "ufw", "tmux", "sudo", "redis-server"
]

ROLE_PACKAGES = {
    "db": [],
    "app": [
        "python2.7", "python2.7-dev", "python-pip", "nginx", "libffi-dev",
        "libxml2", "libxslt1-dev", "supervisor", "libpq-dev", "pgbouncer",
        "libjansson-dev"
    ]
}


