importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-messaging-compat.js');

const firebaseConfig = {
    apiKey: "AIzaSyDBKUnD74xM2Ac2-v6V9TCmBWdjVy5oJsQ",
    authDomain: "matriculas-c9045.firebaseapp.com",
    projectId: "matriculas-c9045",
    storageBucket: "matriculas-c9045.firebasestorage.app",
    messagingSenderId: "349267049309",
    appId: "1:349267049309:web:f5b5015949f9dac29f46b4",
    measurementId: "G-DZBQJD29DN"
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
    console.log('[SW] Notificación en background:', payload);

    const notificationTitle = payload.notification?.title || payload.data?.title;
    const notificationOptions = {
        body: payload.notification?.body || payload.data?.body,
        icon: '/static/matriculas/images/NewLogoSinFondo.png',
        data: payload.data
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();

    const url = event.notification.data?.url || "/";

    event.waitUntil(
        clients.matchAll({ type: "window", includeUncontrolled: true })
        .then(function(clientList) {
            for (const client of clientList) {
                if (client.url.includes(url) && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});