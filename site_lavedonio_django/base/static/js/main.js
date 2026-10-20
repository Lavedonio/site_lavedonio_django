// Same key read by the script in the <head> of base.html, which applies the
// saved theme before the page is drawn
const COLOR_SCHEME_STORAGE_KEY = 'color-scheme';

function get_saved_color_scheme() {
    try {
        return localStorage.getItem(COLOR_SCHEME_STORAGE_KEY) || 'auto';
    } catch(error) {
        return 'auto';
    }
}

function set_color_scheme(scheme) {
    valid_schemes = ['auto', 'light', 'dark'];

    if(!valid_schemes.includes(scheme)) {
        console.log('Invalid color scheme: ' + scheme);
        return 0;
    }

    // Remembers the choice for the next pages and visits
    try { localStorage.setItem(COLOR_SCHEME_STORAGE_KEY, scheme); } catch(error) {}

    // If auto theme is chosen, gets user's default color scheme
    if(scheme !== 'auto') {
        target_scheme = scheme
    }
    else {
        if(window.matchMedia) {
            target_scheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
    }

    // Sets the theme to HTML tag
    document.documentElement.setAttribute('data-bs-theme', target_scheme);

    // Gets all the selector options from the navbar, remove the active state
    // from all of them and readds just to the selected option.
    theme_selectors = {
        "auto": document.querySelector('#automatic-theme'),
        "light": document.querySelector('#light-theme'),
        "dark": document.querySelector('#dark-theme')
    }

    Object.keys(theme_selectors).forEach(theme => {
        theme_selectors[theme].classList.remove('active')
    });

    theme_selectors[scheme].classList.add('active');

    // Updates the svg theme indicators in the navbar to reflect the option chosen:
    // - auto theme: Moon filled / Sun filled
    // - dark theme: Moon filled / Sun not filled
    // - light theme: Moon not filled / Sun filled
    theme_indicators = {
        "light": document.querySelector('#icon-light-mode'),
        "dark": document.querySelector('#icon-dark-mode')
    }

    Object.entries(theme_indicators).forEach(([indicator, indicator_obj]) => {
        raw_href = indicator_obj.firstChild.href;
        href_link = typeof raw_href === 'string' ? raw_href : raw_href['baseVal'];

        if((scheme === 'auto' || scheme === indicator) && !href_link.endsWith('-fill')) {
            href_link += '-fill';
        }
        else if(scheme !== 'auto' && scheme !== indicator && href_link.endsWith('-fill')) {
            href_link = href_link.replace('-fill', '');
        }

        indicator_obj.firstChild.setAttribute('href', href_link);
    });
}

// ------ Cookie consent ------
// Optional cookies (Google Analytics) are only set after the visitor allows
// them, either in the banner or in the cookies menu of the navbar. The choice
// is stored in a cookie, so the server also knows it.
const COOKIE_CONSENT_MAX_AGE = 365 * 24 * 60 * 60;  // 1 year, in seconds

function get_cookie_settings() {
    const element = document.querySelector('#cookie-settings');
    return element ? JSON.parse(element.textContent) : {};
}

function load_analytics(analytics_id) {
    if(!analytics_id) {
        return;
    }
    window['ga-disable-' + analytics_id] = false;
    if(window.gtag) {
        return;
    }

    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(analytics_id);
    document.head.appendChild(script);

    window.dataLayer = window.dataLayer || [];
    window.gtag = function() { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', analytics_id);
}

// Stops analytics and deletes its cookies (_ga, _ga_<id>, _gid), which are set
// on the site's domain or on one of its parent domains
function remove_analytics(analytics_id) {
    if(analytics_id) {
        window['ga-disable-' + analytics_id] = true;
    }

    const names = document.cookie.split(';')
        .map(cookie => cookie.trim().split('=')[0])
        .filter(name => name === '_gid' || name.startsWith('_ga'));
    const domain_parts = window.location.hostname.split('.');

    names.forEach(name => {
        document.cookie = name + '=; Max-Age=0; Path=/';
        for(let i = 0; i < domain_parts.length - 1; i++) {
            document.cookie = name + '=; Max-Age=0; Path=/; Domain=.' + domain_parts.slice(i).join('.');
        }
    });
}

function set_cookie_consent(consent) {
    const settings = get_cookie_settings();
    const secure = window.location.protocol === 'https:' ? '; Secure' : '';
    document.cookie = settings.cookieName + '=' + consent + '; Max-Age=' + COOKIE_CONSENT_MAX_AGE + '; Path=/; SameSite=Lax' + secure;

    document.querySelectorAll('.dropdown-item[data-cookie-consent]').forEach(item => {
        item.classList.toggle('active', item.dataset.cookieConsent === consent);
    });

    const banner = document.querySelector('#cookie-banner');
    if(banner) {
        banner.remove();
    }

    if(consent === 'accepted') {
        load_analytics(settings.analyticsId);
    }
    else {
        remove_analytics(settings.analyticsId);
    }
}

function setup_cookie_consent() {
    document.querySelectorAll('[data-cookie-consent]').forEach(element => {
        element.addEventListener('click', function(event) {
            event.preventDefault();
            set_cookie_consent(element.dataset.cookieConsent);
        });
    });

    const settings = get_cookie_settings();
    if(settings.consent === 'accepted') {
        load_analytics(settings.analyticsId);
    }
}

// Fades in the background photos once they're loaded. Until then, their tiny
// blurred version is shown (see .progressive-background in main.css).
function setup_progressive_backgrounds() {
    document.querySelectorAll('.progressive-background').forEach(element => {
        const match = getComputedStyle(element).getPropertyValue('--background-image').match(/url\(\s*["']?(.+?)["']?\s*\)/);
        if(!match) {
            element.classList.add('progressive-background--loaded');
            return;
        }

        const image = new Image();
        const show = () => element.classList.add('progressive-background--loaded');
        image.addEventListener('load', show);
        image.addEventListener('error', show);
        image.src = match[1];
        if(image.complete) {
            element.classList.add('progressive-background--instant');
            show();
        }
    });
}

// Picks which of the site languages best matches the browser/OS language
// settings. Languages that the site doesn't have fall back to the default one,
// e.g. 'pt-PT' -> 'pt-br', 'es' -> 'en'.
function get_preferred_site_language(site_languages, default_language) {
    const browser_languages = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || ''];

    for(const browser_language of browser_languages) {
        const language = browser_language.toLowerCase();
        const exact_match = site_languages.find(site_language => site_language === language);
        if(exact_match) {
            return exact_match;
        }
        const partial_match = site_languages.find(site_language => site_language.split('-')[0] === language.split('-')[0]);
        if(partial_match) {
            return partial_match;
        }
    }
    return default_language;
}

// Shows a banner offering the version of the page in the visitor's language
// (e.g. lavedonio.com.br for a browser in Portuguese).
function setup_language_banner() {
    const banner = document.querySelector('#language-banner');
    const data_element = document.querySelector('#language-banner-data');
    if(!banner || !data_element) {
        return;
    }

    const data = JSON.parse(data_element.textContent);
    const storage_key = 'language-banner-dismissed';

    // Visitors that arrived using the language menu chose this language on
    // purpose: remembers that and cleans the flag from the address bar.
    const url = new URL(window.location.href);
    if(url.searchParams.has(data.chosenParam)) {
        try { localStorage.setItem(storage_key, 'chosen'); } catch(error) {}
        url.searchParams.delete(data.chosenParam);
        window.history.replaceState(null, '', url.pathname + url.search + url.hash);
    }

    try {
        if(localStorage.getItem(storage_key)) {
            return;
        }
    } catch(error) {}

    const site_languages = [data.current].concat(Object.keys(data.alternates));
    const preferred_language = get_preferred_site_language(site_languages, data.default);
    const alternate = data.alternates[preferred_language];
    if(preferred_language === data.current || !alternate) {
        return;
    }

    banner.setAttribute('lang', preferred_language);
    banner.querySelector('.language-banner__message').textContent = alternate.message;
    const action = banner.querySelector('.language-banner__action');
    action.textContent = alternate.action;
    action.setAttribute('href', alternate.url);
    action.setAttribute('hreflang', preferred_language);
    const dismiss = banner.querySelector('.language-banner__dismiss');
    dismiss.setAttribute('aria-label', alternate.dismiss);
    dismiss.addEventListener('click', function() {
        try { localStorage.setItem(storage_key, 'dismissed'); } catch(error) {}
        banner.hidden = true;
    });

    banner.hidden = false;
}

document.addEventListener("DOMContentLoaded", function() {

    // Hides Navbar when scrolling down and shows it again when scrolling up
    // Code adapted from: https://bootstrap-menu.com/detail-autohide.html
    autohide_elements = document.querySelectorAll('.autohide');
    navbar_toggler_element = document.querySelector('.navbar-toggler');

    // add padding-top to body (if necessary) and shares the navbar's real
    // height with the CSS (--navbar-height), used by the page headers
    navbar_element = document.querySelector('#main-nav');
    function update_navbar_height() {
        document.body.style.paddingTop = navbar_element.offsetHeight + 'px';
        document.documentElement.style.setProperty('--navbar-height', navbar_element.offsetHeight + 'px');
    }
    update_navbar_height();
    window.addEventListener('resize', update_navbar_height);
  
    if(autohide_elements) {
        var last_scroll_top = window.scrollY + 1000;  // forces navbar to always start scrolled down

        window.addEventListener('scroll', function() {
            let scroll_top = window.scrollY;

            // Debug
            // console.log('scroll_top: ' + scroll_top);
            // console.log('last_scroll_top: ' + last_scroll_top);

            if(scroll_top <= 0 || scroll_top < last_scroll_top) {
                autohide_elements.forEach(item => {
                    item.classList.remove('scrolled-down');
                    item.classList.add('scrolled-up');
                });
            }
            else {
                autohide_elements.forEach(item => {
                    item.classList.remove('scrolled-up');
                    item.classList.add('scrolled-down');
                });
            }
            last_scroll_top = scroll_top;
        });

        // Fixes Bootstrap's offcanvas
        navbar_toggler_element.addEventListener('click', function() {
            navbar_element.classList.remove('scrolled-up');
        });
    }

    // Shows Django messages (e.g. "Post saved")
    document.querySelectorAll('.messages-container .toast').forEach(toast => {
        bootstrap.Toast.getOrCreateInstance(toast).show();
    });

    setup_progressive_backgrounds();
    setup_language_banner();
    setup_cookie_consent();

    // Sets color scheme saved in previous pages (defaults to the auto theme setting)
    set_color_scheme(get_saved_color_scheme());

    // The automatic theme follows changes in the OS setting
    if(window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function() {
            if(get_saved_color_scheme() === 'auto') {
                set_color_scheme('auto');
            }
        });
    }

    document.querySelector('#automatic-theme').addEventListener('click', function(event) {
        event.preventDefault();
        set_color_scheme('auto');
    });
    document.querySelector('#light-theme').addEventListener('click', function(event) {
        event.preventDefault();
        set_color_scheme('light');
    });
    document.querySelector('#dark-theme').addEventListener('click', function(event) {
        event.preventDefault();
        set_color_scheme('dark');
    });
});
