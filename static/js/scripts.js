/**
 * AuthSystem — Main JavaScript
 * Cursor tracking, input glow, password toggle, alerts, mobile menu.
 */

document.addEventListener('DOMContentLoaded', function () {

    // ======================================================================
    // 1. Cursor-tracking gradient blob
    // ======================================================================
    const trackingAreas = document.querySelectorAll('[data-track-cursor]');
    trackingAreas.forEach(function (area) {
        const blob = area.querySelector('.gradient-blob');
        if (!blob) return;

        area.addEventListener('mousemove', function (e) {
            const rect = area.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            blob.style.transform = 'translate(' + (x - 250) + 'px, ' + (y - 250) + 'px)';
            blob.style.opacity = '1';
        });

        area.addEventListener('mouseleave', function () {
            blob.style.opacity = '0';
        });
    });

    // ======================================================================
    // 2. Input hover glow effect (top & bottom border)
    // ======================================================================
    const glowInputs = document.querySelectorAll('[data-glow-input]');
    glowInputs.forEach(function (wrapper) {
        const input = wrapper.querySelector('input, textarea, select');
        const topGlow = wrapper.querySelector('.input-glow--top');
        const bottomGlow = wrapper.querySelector('.input-glow--bottom');
        if (!input || !topGlow || !bottomGlow) return;

        function updateGlow(e) {
            const rect = wrapper.getBoundingClientRect();
            const x = e.clientX - rect.left;
            topGlow.style.background =
                'radial-gradient(30px circle at ' + x + 'px 0px, rgb(165, 150, 255) 0%, transparent 70%)';
            bottomGlow.style.background =
                'radial-gradient(30px circle at ' + x + 'px 2px, rgb(165, 150, 255) 0%, transparent 70%)';
        }

        wrapper.addEventListener('mousemove', function (e) {
            topGlow.classList.add('active');
            bottomGlow.classList.add('active');
            updateGlow(e);
        });

        wrapper.addEventListener('mouseleave', function () {
            topGlow.classList.remove('active');
            bottomGlow.classList.remove('active');
        });
    });

    // ======================================================================
    // 3. Password Show/Hide Toggle
    // ======================================================================
    function getEyeSVG(type) {
        if (type === 'eye') {
            return '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
        }
        return '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
    }

    document.querySelectorAll('input[data-pw-toggle="true"]').forEach(function (input) {
        if (input.dataset.pwToggleInit) return;
        input.dataset.pwToggleInit = 'true';

        var wrapper = input.closest('.icon-wrapper') || input.parentElement;
        if (!input.closest('.icon-wrapper')) {
            var pwWrap = input.closest('.pw-wrapper');
            if (pwWrap) wrapper = pwWrap;
        }

        var toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.className = 'password-toggle absolute right-3 top-1/2 -translate-y-1/2 z-20 p-1 rounded-md text-slate-400 hover:text-slate-300 hover:bg-white/5 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-500/50';
        toggle.setAttribute('aria-label', 'Show password');
        toggle.setAttribute('tabindex', '-1');
        toggle.innerHTML = '<span class="eye-icon block">' + getEyeSVG('eye') + '</span><span class="eye-off-icon hidden">' + getEyeSVG('eye-off') + '</span>';

        wrapper.appendChild(toggle);

        toggle.addEventListener('click', function () {
            var isPassword = input.getAttribute('type') === 'password';
            input.setAttribute('type', isPassword ? 'text' : 'password');
            toggle.querySelector('.eye-icon').classList.toggle('hidden', !isPassword);
            toggle.querySelector('.eye-off-icon').classList.toggle('hidden', isPassword);
            toggle.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
        });
    });

    // ======================================================================
    // 4. Toast Notifications
    // ======================================================================
    var toastContainer = document.getElementById('toast-container');

    // SVG icons per type
    var TOAST_ICONS = {
        success: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>',
        error:   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
        warning: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        info:    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    };

    // Map Django message tags to toast types
    function mapTagToType(tags) {
        tags = (tags || '').toLowerCase();
        if (tags.indexOf('error') !== -1 || tags.indexOf('danger') !== -1) return 'error';
        if (tags.indexOf('warning') !== -1) return 'warning';
        if (tags.indexOf('success') !== -1) return 'success';
        return 'info';
    }

    // Duration per type (ms)
    var TOAST_DURATION = {
        success: 4000,
        info:    5000,
        warning: 8000,
        error:   0, // manual dismiss only
    };

    window.showToast = function (type, text) {
        if (!toastContainer) return;

        type = type || 'info';

        var el = document.createElement('div');
        el.className = 'toast toast--' + type;
        el.setAttribute('role', 'alert');

        el.innerHTML =
            '<div class="toast-icon">' + (TOAST_ICONS[type] || TOAST_ICONS.info) + '</div>' +
            '<div class="toast-text">' + text + '</div>' +
            '<button class="toast-close" aria-label="Close">' +
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>' +
            '</button>';

        // Progress bar
        var duration = TOAST_DURATION[type] || 4000;
        if (duration > 0) {
            var progress = document.createElement('div');
            progress.className = 'toast-progress';
            progress.style.animationDuration = duration + 'ms';
            el.appendChild(progress);
        }

        // Close handler
        var closeBtn = el.querySelector('.toast-close');
        closeBtn.addEventListener('click', function () {
            removeToast(el);
        });

        toastContainer.appendChild(el);

        // Auto-remove
        if (duration > 0) {
            setTimeout(function () {
                removeToast(el);
            }, duration);
        }
    };

    function removeToast(el) {
        if (el.dataset.removing) return;
        el.dataset.removing = 'true';
        el.classList.add('removing');
        // After animation completes, remove from DOM
        setTimeout(function () {
            if (el.parentNode) el.parentNode.removeChild(el);
        }, 300);
    }

    // Read Django messages from JSON script tag
    var toastData = document.getElementById('toast-data');
    if (toastData) {
        try {
            var messages = JSON.parse(toastData.textContent);
            messages.forEach(function (msg) {
                var type = mapTagToType(msg.tags);
                showToast(type, msg.text);
            });
        } catch (e) {
            // silent
        }
    }

    // ======================================================================
    // 5. Mobile menu toggle
    // ======================================================================
    window.toggleMobileMenu = function () {
        var menu = document.getElementById('navbarMenu');
        if (menu) menu.classList.toggle('hidden');
    };
});
