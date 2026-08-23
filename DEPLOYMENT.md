# Despliegue v12

La app ya está separada en dos capas:

1. **PWA móvil** (`index.html`, `manifest.webmanifest`, `service-worker.js`)
2. **Backend** (`server/`) que busca, deduplica, registra historial y envía Web Push.

## Requisitos para producción
- Hosting con HTTPS.
- Python 3.
- Programador/cron cada 60 minutos para `server/hourly_runner.py`.
- Variables VAPID configuradas.
- La PWA debe servirse desde HTTPS para que Web Push funcione en Android.

## Seguridad
- No guardar contraseñas de portales en el frontend.
- La clave VAPID privada solo vive en el servidor.
- Las postulaciones automáticas siguen desactivadas hasta validar cada portal.
