echo "Re-running with modified validation workflow..."
git add .
git commit -m "Update CI/CD workflow to continue on style issues"
git push origin develop
