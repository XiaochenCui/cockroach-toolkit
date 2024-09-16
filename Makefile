publish:
	git add --all
	git commit -m "Update" || true
	git push

	cd vscode/extension/optgen-vscode

	# npm install -g @vscode/vsce
	# vsce login XiaochenCui
	vsce package
	vsce publish