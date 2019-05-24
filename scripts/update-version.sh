#!/usr/bin/env bash
VERSION_PART=patch
TEMP_CHANGE_LOG=wip_change.log
NEW_VERSION=$(bumpversion --dry-run --allow-dirty --list $VERSION_PART | grep new_version | sed s,"^.*=",,)
tail -c1 < $TEMP_CHANGE_LOG | read -r || echo >> $TEMP_CHANGE_LOG
echo '--' >> $TEMP_CHANGE_LOG
echo "Version $NEW_VERSION" | cat - $TEMP_CHANGE_LOG | tee $TEMP_CHANGE_LOG
cat $TEMP_CHANGE_LOG ../change.log > tmp
cat tmp > ../change.log
rm tmp
cd ..
#git add . && git commit --file scripts/wip_change.log
git add . && git commit -m "$NEW_VERSION"
cd scripts
> $TEMP_CHANGE_LOG
bumpversion --list $VERSION_PART

