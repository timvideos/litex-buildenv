#!/bin/bash

set -e

TARGETS=${@-$(find * -maxdepth 0 -type d)}

COMMIT_MSG=$(tempfile) || exit
trap "rm -f -- '$COMMIT_MSG'" EXIT

cat > $COMMIT_MSG <<EOF
Updating submodules.

EOF

DIRTY=0
for TARGET in $TARGETS; do
	pushd $TARGET > /dev/null
	VERSION=$(git describe --always --dirty)
	echo -n "$TARGET version ($VERSION) " | grep --color -E "dirty|$"
	if echo $VERSION | grep -q "dirty"; then
		DIRTY=1
	fi
	popd > /dev/null
done

if [ $DIRTY -eq 0 ]; then
	echo "All targets clean, good to update."
else
	echo "Some target are dirty, can't update."
	exit 1
fi

for TARGET in $TARGETS; do
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
		AFTER_VER=$(git describe --always --dirty)
		if [ x"$BEFORE_VER" = x"$AFTER_VER" ]; then
			echo "$TARGET is unchanged"
		else
			echo "Move $TARGET from $BEFORE_VER to $AFTER_VER"
			cat >> $COMMIT_MSG <<EOF
 * $TARGET changed from $BEFORE_VER to $AFTER_VER
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
