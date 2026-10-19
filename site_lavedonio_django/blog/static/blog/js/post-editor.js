// Markdown editor of the blog posts (TOAST UI Editor). It has a WYSIWYG mode
// and a Markdown mode with preview; the Markdown is what gets saved.
document.addEventListener('DOMContentLoaded', function() {
    const Editor = toastui.Editor;
    const MODE_STORAGE_KEY = 'post-editor-mode';
    const editor_language = document.documentElement.lang === 'pt-br' ? 'pt-BR' : 'en-US';
    const editors = [];

    function get_saved_mode() {
        try {
            return localStorage.getItem(MODE_STORAGE_KEY) || 'wysiwyg';
        } catch(error) {
            return 'wysiwyg';
        }
    }

    function get_preview_style() {
        // Side by side preview doesn't fit on phones
        return siteEditor.is_small_screen() ? 'tab' : 'vertical';
    }

    document.querySelectorAll('textarea[data-markdown-editor]').forEach(textarea => {
        const form = siteEditor.get_form(textarea);
        const container = document.createElement('div');
        container.className = 'markdown-editor';
        textarea.after(container);
        textarea.hidden = true;

        const editor = new Editor({
            el: container,
            height: siteEditor.is_small_screen() ? '70vh' : '640px',
            minHeight: '300px',
            initialValue: textarea.value,
            initialEditType: get_saved_mode(),
            previewStyle: get_preview_style(),
            language: editor_language,
            theme: siteEditor.is_dark_theme() ? 'dark' : 'light',
            usageStatistics: false,
            autofocus: false,
            toolbarItems: [
                ['heading', 'bold', 'italic', 'strike'],
                ['hr', 'quote'],
                ['ul', 'ol', 'task', 'indent', 'outdent'],
                ['table', 'image', 'link'],
                ['code', 'codeblock'],
            ],
            hooks: {
                // Images pasted, dropped or chosen are uploaded instead of embedded as base64
                addImageBlobHook: function(blob, callback) {
                    siteEditor.upload_image(form, blob)
                        .then(result => callback(result.url, blob.name ? blob.name.replace(/\.[^.]+$/, '') : ''))
                        .catch(error => window.alert(error.message));
                    return false;
                },
            },
        });

        editor.on('change', function() {
            textarea.value = editor.getMarkdown();
            siteEditor.mark_dirty();
        });

        editor.on('changeMode', function(mode) {
            try { localStorage.setItem(MODE_STORAGE_KEY, mode); } catch(error) {}
        });

        form.addEventListener('submit', function() {
            textarea.value = editor.getMarkdown();
        });

        editors.push({editor: editor, container: container});
    });

    siteEditor.on_theme_change(function(is_dark) {
        editors.forEach(item => {
            item.container.querySelector('.toastui-editor-defaultUI').classList.toggle('toastui-editor-dark', is_dark);
        });
    });

    window.addEventListener('resize', function() {
        const preview_style = get_preview_style();
        editors.forEach(item => {
            if(item.editor.getCurrentPreviewStyle && item.editor.getCurrentPreviewStyle() !== preview_style) {
                item.editor.changePreviewStyle(preview_style);
            }
        });
    });
});
