#!/bin/bash -eu
PROJECT_NAME=$(basename $(git config --local remote.origin.url) |sed "s/\.git$//")
find . -name .git -prune -o -exec sed -i.bk "s/pythonlambdatemplate/${PROJECT_NAME}/g" {} \;
find . -name '*.bk' -exec rm {} \;
mv pythonlambdatemplate ${PROJECT_NAME}
git add .
git ci -am "Convert pythonlambdatemplate to ${PROJECT_NAME}"