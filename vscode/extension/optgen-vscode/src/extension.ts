// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "optgen-vscode" is now active!');

	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	let disposable = vscode.commands.registerCommand('optgen-vscode.helloWorld', () => {
		// The code you place here will be executed every time your command is executed
		// Display a message box to the user
		vscode.window.showInformationMessage('Hello World from optgen-vscode!');
	});

	context.subscriptions.push(disposable);

	context.subscriptions.push(
		vscode.languages.registerDocumentSymbolProvider(
			OPT_MODE, new OptDocumentSymbolProvider()));
}

// This method is called when your extension is deactivated
export function deactivate() { }

const OPT_MODE: vscode.DocumentFilter = { language: 'optgen', scheme: 'file' };

class OptDocumentSymbolProvider implements vscode.DocumentSymbolProvider {
	public provideDocumentSymbols(
		document: vscode.TextDocument, token: vscode.CancellationToken):
		Thenable<vscode.DocumentSymbol[]> {
		let symbols: vscode.DocumentSymbol[] = [];

		let currentSymbol: vscode.DocumentSymbol | undefined = undefined;

		for (let i = 0; i < document.lineCount; i++) {
			let line = document.lineAt(i);

			// skip comments
			if (line.text.startsWith("#")) {
				continue;
			}

			// get tags, syntax: [tag1, tag2, ...]
			let match = line.text.match(/\[(.*?)\]/);
			if (match) {
				let tags = match[1];

				// get tag list, separated by comma
				let tagList = tags.split(',');

				if (tagList.length == 0) {
					continue;
				}

				// if tags contains "Normalize", then it's a normalize rule, the first tag is the name of the rule
				if (tags.includes("Normalize")) {
					let ruleName = tagList[0].trim();
					console.log("Normalize rule: " + ruleName);
					let symbol = new vscode.DocumentSymbol(ruleName, "", vscode.SymbolKind.Function, line.range, line.range);
					symbols.push(symbol);
					continue;
				}
			}

			// if start with "define", then it's a struct definition
			match = line.text.match(/^define\s+(.*?)\s+\{/);
			if (match) {
				let structName = match[1].trim();
				currentSymbol = new vscode.DocumentSymbol(structName, "", vscode.SymbolKind.Struct, line.range, line.range);
				continue;
			}

			// match the fields of struct definition
			if (currentSymbol) {
				match = line.text.match(/^\s+(.*?)\s+(.*?)\s*$/);
				if (match) {
					let fieldName = match[1].trim();
					let fieldType = match[2].trim();

					let field = new vscode.DocumentSymbol(fieldName, fieldType, vscode.SymbolKind.Field, line.range, line.range);
					currentSymbol.children.push(field);
					continue;
				}
			}

			// match the end of struct definition
			if (currentSymbol && line.text.trim() == "}") {
				symbols.push(currentSymbol);
				currentSymbol = undefined;
				continue;
			}
		}

		return new Promise((resolve, reject) => {
			resolve(symbols);
		});
	}
}
