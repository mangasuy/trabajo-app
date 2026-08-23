# Trabajo App v4 — Perfil de búsqueda v1

Esta versión consolida las reglas acordadas antes de continuar con los conectores.

Archivos:
- `index.html`: vista simple del perfil de búsqueda.
- `search_profile.json`: configuración estructurada que usará el motor.

Siguiente etapa: implementar los conectores de los cinco portales contra esta configuración, sin cambiar las reglas del perfil salvo decisión explícita.


## v5 — Buscojobs, primer conector

Se agregó:
- `buscojobs_connector.py`: consulta pública de Buscojobs Uruguay y guarda candidatos.
- `scoring_engine.py`: aplica la configuración acordada (75/50, Montevideo, nocturno, etc.).
- `data/`: salida del conector y del clasificador.

### Prueba
1. Tener Python 3.
2. Ejecutar `python buscojobs_connector.py`
3. Ejecutar `python scoring_engine.py`

### Estado real
La consulta pública de Buscojobs fue verificada el 23/08/2026. El sitio muestra título,
ubicación y antigüedad de ofertas públicamente. Esta versión NO inicia sesión ni envía
postulaciones todavía. El siguiente paso es robustecer el parser de cada ficha para extraer
descripción/requisitos/horario/salario antes de habilitar cualquier postulación automática.


## v6 — lectura completa de Buscojobs
`buscojobs_full_parser.py` abre cada ficha encontrada y extrae texto, ubicación, modalidad, horario, educación, salario visible y requisitos sensibles.

Flujo: `python buscojobs_connector.py` → `python buscojobs_full_parser.py` → scoring.

Aún no envía candidaturas: primero se validan requisitos excluyentes contra el perfil para evitar postulaciones incorrectas.


## v7 — motor de scoring validado
Se agregó `scoring_engine_v2.py`, que separa:
- exclusiones duras;
- requisitos inciertos que bloquean auto-postulación;
- puntuación por tipo de puesto, ubicación, antigüedad, estudios, horario y salario.

`data/validation_offers.json` y `data/validation_results.json` permiten revisar decisiones antes de habilitar envíos.


## v8 — panel visual
El panel `index.html` ahora representa las decisiones del motor como tarjetas:
- verde: 75–100, candidata a postulación;
- ámbar: 50–74, revisión manual inmediata;
- descartada: debajo del umbral o bloqueo duro.

Los botones de postulación permanecen deliberadamente en modo seguro hasta integrar autenticación y envío real.


## v9 — sesión de Buscojobs sin guardar contraseña

Se agregó `buscojobs_session.py` usando un perfil persistente de Chromium.

Funcionamiento:
1. Instalar Playwright: `pip install playwright`
2. Instalar Chromium: `playwright install chromium`
3. Ejecutar `python buscojobs_session.py`
4. Iniciar sesión manualmente en Buscojobs.
5. La sesión queda reutilizable en el perfil local del navegador.

La app no recibe ni almacena la contraseña. Buscojobs indica que para postular se debe
iniciar sesión y que la candidatura se realiza con el perfil/CV del candidato.

`open_application.py` permite abrir una oferta clasificada para intervención manual,
pero todavía no envía ninguna candidatura.


## v10 — flujo móvil
Se convirtió el panel a enfoque móvil/PWA:
- navegación inferior;
- alertas prioritarias;
- filtros Para postular / Revisar;
- apertura de la oferta original en el navegador móvil;
- configuración de búsqueda cada 60 minutos;
- las ofertas <50% no aparecen en el flujo principal.

La búsqueda horaria real debe ejecutarse en un servidor; una PWA cerrada en Android no puede
garantizar scraping cada hora. La v10 deja separadas interfaz móvil y tarea de servidor.


## v11 — backend, historial y deduplicación
Nuevo backend local/servidor en `server/`:
- `db.py`: SQLite con ofertas, estados y alertas.
- `pipeline.py`: guarda ofertas nuevas y evita duplicados.
- `api.py`: API simple para móvil (`/api/offers`, `/api/alerts`).
- `hourly_runner.py`: pipeline previsto para ejecutarse cada 60 minutos en servidor.

Estados persistentes:
`new`, `reviewing`, `manual_required`, `applied`, `dismissed`.

Las ofertas descartadas no generan alertas.
Una oferta ya conocida no vuelve a generar una alerta nueva cada hora.

### Prueba local
Desde la carpeta:
`python server/api.py`
Luego abrir:
`http://127.0.0.1:8787/api/alerts`

### Siguiente etapa
Implementar notificaciones push reales para Android/PWA y desplegar este backend en un servidor.


## v12 — PWA instalable + Web Push
Se agregó:
- `service-worker.js`: caché básico + recepción de notificaciones.
- botón **Activar alertas** y **Instalar app**.
- endpoint `/api/push/subscribe`.
- almacenamiento de suscripciones push.
- envío Web Push mediante `pywebpush`.
- `.env.example`, `requirements.txt` y `DEPLOYMENT.md`.

Para que las notificaciones funcionen fuera del entorno local hace falta desplegar el proyecto
en un hosting HTTPS y configurar claves VAPID. La lógica ya está preparada.


## v13 — listo para Railway
La PWA y el backend ahora corren en un único servicio.
`server/app.py` sirve la interfaz, API y ejecuta el pipeline cada hora.
SQLite usa el volumen Railway si existe (`RAILWAY_VOLUME_MOUNT_PATH` o `DATA_DIR`).
Ver `RAILWAY_DEPLOY.md`.


## v14 — arquitectura gratuita
Ver `FREE_DEPLOY.md`. GitHub Pages + Actions + Supabase reemplazan el hosting pago.


## v14.1 — Supabase conectado
`config.js` ya contiene el Project URL y la Publishable Key del proyecto Trabajo.
La service role key NO está incluida y nunca debe publicarse en GitHub Pages.
