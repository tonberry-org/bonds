#!/bin/bash -eu
PROJECT_NAME=$(basename $(git config --local remote.origin.url) |sed "s/\.git$//")
find . -name .git -prune -o -exec sed -i.bk "s/bonds/${PROJECT_NAME}/g" {} \;
find . -name '*.bk' -exec rm {} \;
mv bonds ${PROJECT_NAME}
git add .
git ci -am "Convert bonds to ${PROJECT_NAME}"