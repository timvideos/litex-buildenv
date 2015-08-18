

(
	cd build/migen
	git fetch origin
	git checkout origin/master
)
MIGEN_VERSION=$(cd build/migen; git describe --always --dirty)
git add build/migen

(
	cd build/misoc
	git fetch origin
	git checkout origin/master
)
MISOC_VERSION=$(cd build/misoc; git describe --always --dirty)
git add build/misoc

echo "migen now $MIGEN_VERSION"
echo "misoc now $MISOC_VERSION"

cat << EOF
git commit -F- <<EOF
Updating migen+misoc submodules
 * migen to $MIGEN_VERSION
 * misoc to $MISOC_VERSION
EOF
