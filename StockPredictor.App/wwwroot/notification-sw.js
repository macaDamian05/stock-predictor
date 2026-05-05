self.addEventListener("install", event => {
    event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", event => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener("notificationclick", event => {
    event.notification.close();

    event.waitUntil((async () => {
        const targetUrl = event.notification?.data?.url || "/";
        const clients = await self.clients.matchAll({
            type: "window",
            includeUncontrolled: true
        });

        for (const client of clients) {
            if ("focus" in client) {
                await client.focus();
                return;
            }
        }

        if ("openWindow" in self.clients) {
            await self.clients.openWindow(targetUrl);
        }
    })());
});
