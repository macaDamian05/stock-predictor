window.stockPredictorNotifications = (() => {
    let registrationPromise = null;

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
            if (!("Notification" in window) || window.Notification.permission !== "granted") {
                return false;
            }

            const notificationOptions = {
                body: options?.body || "",
                tag: options?.tag || "stockpredictor",
                icon: "/favicon.png",
                badge: "/favicon.png",
                requireInteraction: !!options?.requireInteraction,
                data: {
                    url: window.location.href
                }
            };

            try {
                const registration = await getServiceWorkerRegistration();
                if (registration && typeof registration.showNotification === "function") {
                    await registration.showNotification(title, notificationOptions);
                    return true;
                }
            } catch {
                // Fall back to the direct browser constructor.
            }

            try {
                const notification = new window.Notification(title, notificationOptions);

                window.setTimeout(() => {
                    try {
                        notification.close();
                    } catch {
                        // Ignore close errors.
                    }
                }, options?.requireInteraction ? 12000 : 7000);

                return true;
            } catch {
                return false;
            }
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
