#!/bin/bash

install_apt_pkg () {
  PKG_OK=$(dpkg-query -W --showformat='${Status}\n' $1|grep "install ok installed")
  if [ "" == "$PKG_OK" ]; then
    echo "Installing package: $1"
    sudo apt-get --yes install $1
  fi
}


setup_git_hooks () {
  # Setup git hooks and shtuff
  if [ ! -L ".git/hooks/pre-commit" ]; then
    echo "Installing and configuring git-hooks"
    install_apt_pkg "pylint"
    exec .hooks/install
  fi
}

main () {
  echo "Setting up development enviroment..."
  setup_git_hooks
  echo "DONE"
}
main

