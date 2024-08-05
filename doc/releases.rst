# Cutting a new release

1. Update the version number in `version.py` using semver versioning rules.
2. Tag your commit with the new version number. ie `git tag -a v0.1.0.dev0 -m "v0.1.0.dev0"` or `git tag -a v0.1.0 -m "v0.1.0" <commit hash>`
3. Push the tag to GitHub. `git push origin v0.1.0`
4. Install twine and install build. `pip install twine` and `pip install build`
5. Build the package. `python -m build`
6. Upload the package to test.pypi.org. `twine upload --repository testpypi dist/*` and verify you can install the test package.
7. Upload the package to pypi.org. `twine upload dist/*` and verify you can install the package.
8. Create a new release on GitHub.
