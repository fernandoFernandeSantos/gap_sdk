#!/bin/bash

git diff --cached > /home/fernando/git_research/gvsocfi/gvsofi.patch

cd /home/fernando/git_research/gvsocfi || exit
git add gvsofi.patch
git commit -m "update on patch"
git push
cd - || exit


#TO apply the patch download the commit f0a594c2a6272837e5b4aedc0aa4985952ab40ac from gap_sdk
# then run git apply /home/fernando/git_research/gvsocfi/gvsofi.patch in the gap_sdk root
