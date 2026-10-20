// Shared behavior of the editor pages (blog posts and projects): language
// tabs, cover image preview, unsaved changes warning and helpers used by the
// rich text editors (image upload and dark mode).

window.siteEditor = (function() {

    function is_dark_theme() {
        return document.documentElement.getAttribute('data-bs-theme') === 'dark';
    }

    // Calls `callback(is_dark)` whenever the theme is changed in the navbar
    function on_theme_change(callback) {
        new MutationObserver(() => callback(is_dark_theme())).observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['data-bs-theme'],
        });
    }

    function get_form(element) {
        return element.closest('form');
    }

    function get_csrf_token(form) {
        const input = form.querySelector('input[name="csrfmiddlewaretoken"]');
        return input ? input.value : '';
    }

    // Uploads an image to the site and returns its URL
    async function upload_image(form, file) {
        const data = new FormData();
        data.append('image', file, file.name || 'image.png');

        const response = await fetch(form.dataset.uploadUrl, {
            method: 'POST',
            headers: {'X-CSRFToken': get_csrf_token(form)},
            body: data,
            credentials: 'same-origin',
        });
        const result = await response.json().catch(() => ({}));

        if(!response.ok || !result.url) {
            throw new Error(result.error || form.dataset.uploadErrorMessage || 'Upload failed');
        }
        return result;
    }

    function is_small_screen() {
        return window.matchMedia('(max-width: 991.98px)').matches;
    }

    let is_dirty = false;

    function mark_dirty() {
        is_dirty = true;
    }

    function setup_translation_panes(form) {
        form.querySelectorAll('[data-translation-pane]').forEach(pane => {
            const toggle = pane.querySelector('[data-translation-toggle]');
            const fields = pane.querySelector('[data-translation-fields]');
            const warning = pane.querySelector('[data-translation-delete-warning]');
            const tab = form.querySelector(`[data-bs-target="#${pane.id}"]`);
            const status = tab ? tab.querySelector('[data-translation-status]') : null;
            const exists = pane.hasAttribute('data-translation-exists');

            function update() {
                fields.classList.toggle('translation-panes__fields--disabled', !toggle.checked);
                fields.inert = !toggle.checked;
                if(status) {
                    status.classList.toggle('translation-tabs__status--enabled', toggle.checked);
                }
                if(warning) {
                    warning.hidden = toggle.checked || !exists;
                }
            }

            toggle.addEventListener('change', update);
            update();
        });
    }

    function setup_cover_preview(form) {
        const input = form.querySelector('[data-cover-input]');
        const preview = form.querySelector('[data-cover-preview]');
        if(!input || !preview) {
            return;
        }
        input.addEventListener('change', function() {
            const file = input.files[0];
            if(file) {
                preview.src = URL.createObjectURL(file);
                preview.hidden = false;
            }
        });
    }

    function setup_unsaved_changes_warning(form) {
        form.addEventListener('input', mark_dirty);
        form.addEventListener('change', mark_dirty);
        form.addEventListener('submit', () => { is_dirty = false; });

        window.addEventListener('beforeunload', function(event) {
            if(is_dirty) {
                event.preventDefault();
                event.returnValue = '';
            }
        });
    }

    // Shows the tab of the first language with errors after a failed submit
    function show_first_tab_with_errors(form) {
        const tab = form.querySelector('.translation-tabs__link--error');
        if(tab) {
            bootstrap.Tab.getOrCreateInstance(tab).show();
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('form[data-editor-form]').forEach(form => {
            setup_translation_panes(form);
            setup_cover_preview(form);
            setup_unsaved_changes_warning(form);
            show_first_tab_with_errors(form);
        });
    });

    return {
        get_form: get_form,
        is_dark_theme: is_dark_theme,
        is_small_screen: is_small_screen,
        mark_dirty: mark_dirty,
        on_theme_change: on_theme_change,
        upload_image: upload_image,
    };
})();
