"""Original experimental Darkelf YouTube player ad filtering.

Install on each HardenedWebPage before its first navigation.
Live YouTube playback still needs developer testing.

This module does not block CNN ads or video/CDN hosts.
"""

from __future__ import annotations

SCRIPT_NAME = "darkelf-original-video-adblock-v1"

VIDEO_ADBLOCK_JS = r"""
(() => {
    'use strict';

    const hosts = new Set([
        'youtube.com',
        'www.youtube.com',
        'm.youtube.com'
    ]);

    if (
        location.protocol !== 'https:' ||
        !hosts.has(location.hostname)
    ) {
        return;
    }

    const marker = Symbol.for('darkelf.videoAdblock.v1');

    if (window[marker]) return;
    window[marker] = true;

    // Preserve content, stream URLs, captions and playability.
    // Remove selected ad fields only from identifiable player data.
    function cleanPlayer(value) {
        if (
            !value ||
            typeof value !== 'object' ||
            Array.isArray(value)
        ) {
            return value;
        }

        const details = value.videoDetails;

        if (
            !details ||
            typeof details.videoId !== 'string' ||
            !value.playabilityStatus
        ) {
            return value;
        }

        for (const key of [
            'playerAds',
            'adPlacements',
            'adSlots'
        ]) {
            if (
                Object.prototype.hasOwnProperty.call(value, key)
            ) {
                delete value[key];
            }
        }

        return value;
    }

    function cleanResult(value) {
        cleanPlayer(value);

        if (
            value &&
            typeof value === 'object' &&
            value.playerResponse
        ) {
            cleanPlayer(value.playerResponse);
        }

        return value;
    }

    const originalParse = JSON.parse;

    JSON.parse = function (...args) {
        return cleanResult(
            Reflect.apply(originalParse, this, args)
        );
    };

    // Fetch's JSON decoder does not necessarily use JSON.parse.
    if (typeof Response !== 'undefined') {
        const originalDecode = Response.prototype.json;

        Response.prototype.json = function (...args) {
            let playerEndpoint = false;

            try {
                const url = new URL(this.url);

                playerEndpoint = (
                    hosts.has(url.hostname) &&
                    url.pathname === '/youtubei/v1/player'
                );
            } catch (_) {
                // Responses without URLs keep normal behavior.
            }

            const pending = Reflect.apply(
                originalDecode,
                this,
                args
            );

            return playerEndpoint
                ? pending.then(cleanResult)
                : pending;
        };
    }

    // Handle the initial player response from inline page scripts.
    const descriptor = Object.getOwnPropertyDescriptor(
        window,
        'ytInitialPlayerResponse'
    );

    if (
        !descriptor ||
        (descriptor.configurable && 'value' in descriptor)
    ) {
        let initial = cleanResult(
            descriptor ? descriptor.value : undefined
        );

        Object.defineProperty(
            window,
            'ytInitialPlayerResponse',
            {
                configurable: true,
                enumerable: descriptor
                    ? descriptor.enumerable
                    : true,

                get() {
                    return initial;
                },

                set(value) {
                    initial = cleanResult(value);
                }
            }
        );
    }

    // Use available Skip controls only while the player reports an ad.
    // Do not seek, accelerate, mute or replace the video stream.
    let scheduled = false;
    let observer = null;
    let stopped = false;

    const attempted = new WeakSet();

    function scan() {
        scheduled = false;

        if (stopped) return;

        const player = document.getElementById('movie_player');

        if (
            !player ||
            !player.classList.contains('ad-showing')
        ) {
            return;
        }

        const selectors = [
            '.ytp-ad-skip-button',
            '.ytp-ad-skip-button-modern',
            '.ytp-skip-ad-button'
        ].join(', ');

        for (
            const button of player.querySelectorAll(selectors)
        ) {
            if (
                button.disabled ||
                button.getAttribute('aria-disabled') === 'true'
            ) {
                continue;
            }

            if (
                !button.getClientRects().length ||
                attempted.has(button)
            ) {
                continue;
            }

            const style = getComputedStyle(button);

            if (
                style.visibility !== 'visible' ||
                style.display === 'none'
            ) {
                continue;
            }

            attempted.add(button);
            button.click();
            break;
        }
    }

    function schedule() {
        if (stopped || scheduled) return;

        scheduled = true;
        setTimeout(scan, 250);
    }

    function start() {
        if (observer || !document.documentElement) return;

        stopped = false;
        observer = new MutationObserver(schedule);

        observer.observe(document.documentElement, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: [
                'class',
                'disabled',
                'aria-disabled',
                'style'
            ]
        });

        schedule();
    }

    if (document.readyState === 'loading') {
        document.addEventListener(
            'DOMContentLoaded',
            start,
            {once: true}
        );
    } else {
        start();
    }

    window.addEventListener('pagehide', () => {
        stopped = true;

        if (observer) {
            observer.disconnect();
        }

        observer = null;
    });

    window.addEventListener('pageshow', start);
})();
"""


def install_video_adblock(page, *, enabled: bool = True) -> None:
    """Register once per page; changes apply on the next document load."""
    from PySide6.QtWebEngineCore import QWebEngineScript

    scripts = page.scripts()

    for existing in scripts.find(SCRIPT_NAME):
        scripts.remove(existing)

    if not enabled:
        return

    script = QWebEngineScript()
    script.setName(SCRIPT_NAME)
    script.setSourceCode(VIDEO_ADBLOCK_JS)
    script.setInjectionPoint(
        QWebEngineScript.InjectionPoint.DocumentCreation
    )
    script.setWorldId(
        QWebEngineScript.ScriptWorldId.MainWorld
    )
    script.setRunsOnSubFrames(False)

    scripts.insert(script)
