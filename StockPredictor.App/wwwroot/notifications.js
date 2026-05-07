window.stockPredictorNotifications = (() => {
    let registrationPromise = null;

    function buildNotificationOptions(options) {
        return {
            body: options?.body || "",
            tag: options?.tag || "stockpredictor",
            icon: "/favicon.png",
            badge: "/favicon.png",
            requireInteraction: !!options?.requireInteraction,
            data: {
                url: window.location.href
            }
        };
    }

    async function showDirectNotification(title, notificationOptions) {
        try {
            const notification = new window.Notification(title, notificationOptions);

            window.setTimeout(() => {
                try {
                    notification.close();
                } catch {
                    // Ignore close errors.
                }
            }, notificationOptions.requireInteraction ? 12000 : 7000);

            return true;
        } catch {
            return false;
        }
    }

    async function showServiceWorkerNotification(title, notificationOptions) {
        try {
            const registration = await getServiceWorkerRegistration();
            if (registration && typeof registration.showNotification === "function") {
                await registration.showNotification(title, notificationOptions);
                return true;
            }
        } catch {
            // Fall back to the direct browser constructor.
        }

        return false;
    }

    async function showNotification(title, options, preferDirect) {
        if (!("Notification" in window) || window.Notification.permission !== "granted") {
            return false;
        }

        const notificationOptions = buildNotificationOptions(options);

        if (preferDirect) {
            if (await showDirectNotification(title, notificationOptions)) {
                return true;
            }

            return await showServiceWorkerNotification(title, notificationOptions);
        }

        if (await showServiceWorkerNotification(title, notificationOptions)) {
            return true;
        }

        return await showDirectNotification(title, notificationOptions);
    }

    async function ensureServiceWorkerRegistration() {
        if (!("serviceWorker" in navigator) || window.isSecureContext !== true) {
            return null;
        }

        if (!registrationPromise) {
            registrationPromise = navigator.serviceWorker
                .register("/notification-sw.js", { scope: "/" })
                .then(async registration => {
                    try {
                        await navigator.serviceWorker.ready;
                    } catch {
                        // Ignore readiness errors and return the registration we have.
                    }

                    return registration;
                })
                .catch(() => null);
        }

        return await registrationPromise;
    }

    async function getServiceWorkerRegistration() {
        if (!("serviceWorker" in navigator) || window.isSecureContext !== true) {
            return null;
        }

        try {
            const existingRegistration = await navigator.serviceWorker.getRegistration();
            if (existingRegistration) {
                return existingRegistration;
            }
        } catch {
            // Ignore getRegistration errors and fall back to a fresh registration attempt.
        }

        return await ensureServiceWorkerRegistration();
    }

    async function getEnvironmentStatus() {
        const registration = await getServiceWorkerRegistration();

        return {
            notificationApiSupported: "Notification" in window,
            serviceWorkerSupported: "serviceWorker" in navigator,
            hasServiceWorkerRegistration: !!registration,
            isSecureContext: window.isSecureContext === true
        };
    }

    return {
        getPermissionStatus: function () {
            if (!("Notification" in window)) {
                return "unsupported";
            }

            return window.Notification.permission || "default";
        },
        getEnvironmentStatus: async function () {
            return await getEnvironmentStatus();
        },
        requestPermission: async function () {
            if (!("Notification" in window)) {
                return "unsupported";
            }

            try {
                const permission = await window.Notification.requestPermission();
                if (permission === "granted") {
                    await ensureServiceWorkerRegistration();
                }

                return permission;
            } catch {
                return window.Notification.permission || "default";
            }
        },
        show: async function (title, options) {
            return await showNotification(title, options, false);
        },
        triggerTestClick: async function () {
            if (!("Notification" in window)) {
                return false;
            }

            if (window.Notification.permission === "default") {
                try {
                    const permission = await window.Notification.requestPermission();
                    if (permission !== "granted") {
                        return false;
                    }

                    try {
                        window.localStorage.setItem("stockpredictor-notifications-enabled-v1", "true");
                    } catch {
                        // Ignore storage errors and continue with the popup test.
                    }
                } catch {
                    return false;
                }
            }

            return await showNotification(
                "Testbenachrichtigung",
                {
                    body: "Dies ist eine neutrale lokale Statusmeldung der Stock-Predictor-App.",
                    tag: "test",
                    requireInteraction: true
                },
                true
            );
        },
        getEnabled: function () {
            try {
                return window.localStorage.getItem("stockpredictor-notifications-enabled-v1") === "true";
            } catch {
                return false;
            }
        },
        setEnabled: function (isEnabled) {
            try {
                window.localStorage.setItem("stockpredictor-notifications-enabled-v1", isEnabled ? "true" : "false");
            } catch {
                // Ignore storage errors and keep the current in-memory state.
            }
        },
        getState: function () {
            try {
                const raw = window.localStorage.getItem("stockpredictor-notifications-state-v1");
                if (!raw) {
                    return {
                        lastPayloadGeneratedAt: null,
                        watchlistDataMarkers: {}
                    };
                }

                const parsed = JSON.parse(raw);
                return parsed && typeof parsed === "object"
                    ? parsed
                    : {
                        lastPayloadGeneratedAt: null,
                        watchlistDataMarkers: {}
                    };
            } catch {
                return {
                    lastPayloadGeneratedAt: null,
                    watchlistDataMarkers: {}
                };
            }
        },
        setState: function (state) {
            try {
                const normalized = state && typeof state === "object"
                    ? state
                    : {
                        lastPayloadGeneratedAt: null,
                        watchlistDataMarkers: {}
                    };

                window.localStorage.setItem("stockpredictor-notifications-state-v1", JSON.stringify(normalized));
            } catch {
                // Ignore storage errors and keep the current in-memory state.
            }
        }
    };
})();

window.addEventListener("load", () => {
    if (window.stockPredictorNotifications?.getEnvironmentStatus) {
        window.stockPredictorNotifications.getEnvironmentStatus().catch(() => {
            // Ignore eager registration errors.
        });
    }
});
