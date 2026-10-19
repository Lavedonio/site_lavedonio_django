// HTML editor of the projects (Jodit). It has a WYSIWYG mode and a source
// code mode (the "</>" button) for editing the HTML directly.
document.addEventListener('DOMContentLoaded', function() {
    const editor_language = document.documentElement.lang === 'pt-br' ? 'pt_br' : 'en';
    const editors = [];

    document.querySelectorAll('textarea[data-html-editor]').forEach(textarea => {
        const form = siteEditor.get_form(textarea);
        const small_screen = siteEditor.is_small_screen();

        const editor = Jodit.make(textarea, {
            language: editor_language,
            theme: siteEditor.is_dark_theme() ? 'dark' : 'default',
            height: small_screen ? '70vh' : 640,
            minHeight: 300,
            toolbarSticky: false,
            toolbarAdaptive: true,
            // A plain textarea is easier to use than the code editor on touch screens
            sourceEditor: small_screen ? 'area' : 'ace',
            beautifyHTML: true,
            askBeforePasteHTML: false,
            askBeforePasteFromWord: false,
            defaultActionOnPaste: 'insert_clear_html',
            showCharsCounter: false,
            showWordsCounter: true,
            showXPathInStatusbar: false,
            // Inserted images keep their size, limited by the page's CSS to the content width
            imageDefaultWidth: null,
            // Toolbars for wide, medium, small and phone sized editors. The
            // buttons left out of the smaller ones are under the "⋮" button.
            buttons: [
                'paragraph', 'bold', 'italic', 'underline', 'strikethrough', '|',
                'ul', 'ol', 'indent', 'outdent', 'align', '|',
                'link', 'image', 'video', 'table', 'hr', '|',
                'brush', 'eraser', 'symbols', '|',
                'undo', 'redo', 'source', 'fullsize',
            ],
            buttonsMD: [
                'paragraph', 'bold', 'italic', 'underline', '|',
                'ul', 'ol', 'align', '|',
                'link', 'image', 'table', '|',
                'undo', 'redo', 'source', 'dots',
            ],
            buttonsSM: [
                'paragraph', 'bold', 'italic', '|',
                'ul', 'ol', '|',
                'link', 'image', '|',
                'source', 'dots',
            ],
            buttonsXS: [
                'paragraph', 'bold', 'italic', '|',
                'ul', 'link', 'image', '|',
                'source', 'dots',
            ],
            // Images are uploaded to the site instead of embedded as base64
            uploader: {
                url: form.dataset.uploadUrl,
                headers: {'X-CSRFToken': form.querySelector('input[name="csrfmiddlewaretoken"]').value},
                filesVariableName: () => 'image',
                insertImageAsBase64URI: false,
                isSuccess: response => Boolean(response.url),
                getMessage: response => response.error || form.dataset.uploadErrorMessage,
                process: response => ({files: [response.url], baseurl: '', isImages: [true]}),
            },
        });

        editor.events.on('change', siteEditor.mark_dirty);
        editors.push(editor);
    });

    siteEditor.on_theme_change(function(is_dark) {
        editors.forEach(editor => {
            editor.container.classList.toggle('jodit_theme_dark', is_dark);
            editor.container.classList.toggle('jodit_theme_default', !is_dark);
        });
    });
});
