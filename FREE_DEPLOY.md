# Trabajo v14 — despliegue gratuito

Arquitectura:

- GitHub Pages: PWA móvil y HTTPS.
- GitHub Actions: ejecuta la búsqueda una vez por hora.
- Supabase Free: ofertas, historial y alertas.

## Lo que queda por configurar una sola vez

### Supabase
1. Crear proyecto gratuito.
2. Abrir SQL Editor y ejecutar `supabase_schema.sql`.
3. Copiar Project URL y anon/public key a `config.js`.
4. Guardar como secretos de GitHub:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`

La service-role key nunca debe ponerse en `config.js`.

### GitHub
1. Crear repositorio.
2. Subir esta carpeta a la rama `main`.
3. Settings → Pages → Source: GitHub Actions.
4. Los workflows incluidos publican la PWA y ejecutan el buscador cada hora.

## Importante
GitHub avisa que los workflows programados pueden retrasarse en períodos de alta carga.
Por eso “cada hora” significa una ejecución horaria programada, no una garantía al minuto exacto.

## Coste
La arquitectura está diseñada para permanecer dentro de los planes gratuitos durante esta etapa.
