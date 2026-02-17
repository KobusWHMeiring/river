#!/bin/bash
echo "Current branch: $(git branch --show-current)"
echo "Uncommitted changes:"
git status --short
echo "Ahead/behind master:"
git log --oneline master..HEAD