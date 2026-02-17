#!/bin/bash
echo "Available branches:"
git branch
echo "Enter branch to switch to:"
read branch
git checkout $branch