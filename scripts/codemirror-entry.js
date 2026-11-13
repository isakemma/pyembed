// Everything embed.js uses from CodeMirror, bundled by scripts/vendor.mjs into
// vendor/codemirror.js. Add a name here (and run `npm run vendor`) to use more.
export { EditorView, basicSetup } from 'codemirror';
export { EditorState } from '@codemirror/state';
export { python } from '@codemirror/lang-python';
export { syntaxHighlighting, HighlightStyle } from '@codemirror/language';
export { tags } from '@lezer/highlight';
export { ViewPlugin, Decoration, MatchDecorator, keymap } from '@codemirror/view';
export { indentWithTab } from '@codemirror/commands';
export { acceptCompletion } from '@codemirror/autocomplete';
