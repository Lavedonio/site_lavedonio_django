document.addEventListener("DOMContentLoaded", function() {

    // Native share sheet (mostly on smartphones)
    document.querySelectorAll('[data-native-share]').forEach(button => {
        if(!navigator.share) {
            return;
        }
        button.hidden = false;
        button.addEventListener('click', function() {
            navigator.share({title: button.dataset.shareTitle, url: button.dataset.shareUrl}).catch(() => {});
        });
    });

    document.querySelectorAll('[data-copy-link]').forEach(button => {
        button.addEventListener('click', function() {
            navigator.clipboard.writeText(button.dataset.copyLink).then(() => {
                const tooltip = bootstrap.Tooltip.getOrCreateInstance(button, {title: button.dataset.copiedMessage, trigger: 'manual'});
                tooltip.show();
                setTimeout(() => tooltip.hide(), 1500);
            });
        });
    });
});
