#!/bin/bash

set -e

TARGETS=${@-$(find * -maxdepth 0 -type d)}

COMMIT_MSG=$(tempfile) || exit
trap "rm -f -- '$COMMIT_MSG'" EXIT

MODULES=()
for TARGET in $TARGETS; do
	if [ ! -e $TARGET/.git ] || ! grep -q "gitdir:" $TARGET/.git 2> /dev/null; then
		echo "Skipping $TARGET as not submodule"
		continue
	else
		echo "Submodule $TARGET"
		MODULES+=("$TARGET")
	fi
	git submodule sync --recursive -- $TARGET
	git submodule update --recursive --init $TARGET
done

echo
echo "Found submodules:"
declare -p MODULES
echo

cat > $COMMIT_MSG <<EOF
Updating submodules.

EOF

DIRTY=0
for TARGET in ${MODULES[@]}; do
	pushd $TARGET > /dev/null
	VERSION=$(git describe --always --dirty)
	echo -n "$TARGET version ($VERSION) " | grep --color -E "dirty|$"
	if echo $VERSION | grep -q "dirty"; then
		DIRTY=1
	fi
	popd > /dev/null
done

if [ $DIRTY = 0 ]; then
	echo "All targets clean, good to update."
else
	echo "Some target are dirty, can't update."
	exit 1
fi

for TARGET in ${MODULES[@]}; do
	(
		case $TARGET in
		*)
			BRANCH=master
			;;
		esac

		cd $TARGET
		echo
		echo "$TARGET checking for updates.."
		BEFORE_VER=$(git describe --always --dirty)
		git fetch origin | sed -e's/^/    /'
		git checkout origin/$BRANCH | sed -e's/^/    /'
		git submodule update --recursive --init
		AFTER_VER=$(git describe --always --dirty)
		if echo $AFTER_VER | grep -q "dirty"; then
			echo "Updated version is dirty!?"
			exit 1
		fi
		if [ x"$BEFORE_VER" = x"$AFTER_VER" ]; then
			echo "$TARGET is unchanged"
		else
			echo "Move $TARGET from $BEFORE_VER to $AFTER_VER"
			cat >> $COMMIT_MSG <<EOF
 * $TARGET changed from $BEFORE_VER to $AFTER_VER
$(git log --graph --pretty=format:'%h - %s <%an>' --no-color --abbrev-commit $BEFORE_VER..$AFTER_VER | sed -e's/^/    /')

EOF
		fi
		echo
	)
	git add $TARGET
done

cat >> $COMMIT_MSG <<EOF

Full submodule status
--
EOF
git submodule status >> $COMMIT_MSG
echo "" >> $COMMIT_MSG

git commit -F- < $COMMIT_MSG
