#!/bin/bash
echo "Enter feature name:"
read feature
git checkout -b "feature/$feature"
echo "Created and switched to feature/$feature"