#!/usr/bin/env bash
NEW_VERSION=$(bumpversion --dry-run --allow-dirty --list patch | grep new_version | sed s,"^.*=",,)
sed -i -e '$a\'  wip_change.log
echo '--' >> wip_change.log
echo "Version $NEW_VERSION" | cat - wip_change.log | tee wip_change.log
cat wip_change.log ../change.log > tmp
cat tmp > ../change.log
rm tmp
cd ..
git add . && git commit --file scripts/wip_change.log
cd scripts
> wip_change.log
bumpversion --list patch

