for x in `find -maxdepth 1 -mindepth 1 -type f -or -path "*.svn*" -prune -or -print`; do cd $x; make clean; cd $q/demo; done
