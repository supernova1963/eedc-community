# EEDC Community - Deployment via Portainer

## Schritt 1: Dateien auf Docker-VM kopieren

```bash
# Von deinem lokalen Rechner:
scp -r /home/gernot/claude/eedc-community gernot@192.168.1.3:/opt/
```

Oder falls du SSH-Zugang hast:
```bash
# Auf der Docker-VM:
cd /opt
git clone <repo-url> eedc-community
```

## Schritt 2: Frontend bauen

```bash
ssh gernot@192.168.1.3

cd /opt/eedc-community/frontend
npm install
npm run build
```

Das Frontend wird nach `/opt/eedc-community/backend/static/` gebaut.

## Schritt 3: Docker Image bauen

```bash
cd /opt/eedc-community
docker build -t eedc-community-api:latest ./backend
```

Prüfen ob das Image erstellt wurde:
```bash
docker images | grep eedc-community
```

## Schritt 4: Stack in Portainer erstellen

1. **Portainer öffnen**: https://192.168.1.3:9443

2. **Stacks → Add stack**

3. **Name**: `eedc-community`

4. **Build method**: Web editor

5. **Compose-Inhalt einfügen** (aus `docker-compose.portainer.yml`):

```yaml
version: "3.8"

services:
  api:
    image: eedc-community-api:latest
    container_name: eedc-community-api
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql+asyncpg://eedc:${POSTGRES_PASSWORD}@db:5432/eedc_community
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-https://energy.raunet.eu}
    depends_on:
      db:
        condition: service_healthy
    networks:
      - internal
      - nginxproxymanager_default

  db:
    image: postgres:16-alpine
    container_name: eedc-community-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=eedc
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=eedc_community
    volumes:
      - eedc_community_postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U eedc -d eedc_community"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - internal

volumes:
  eedc_community_postgres:

networks:
  internal:
    driver: bridge
  nginxproxymanager_default:
    external: true
```

6. **Environment variables** (unten auf der Seite):

   | Name | Value |
   |------|-------|
   | `POSTGRES_PASSWORD` | `dein_sicheres_passwort_hier` |
   | `SECRET_KEY` | `dein_zufaelliger_string_hier` |
   | `ALLOWED_ORIGINS` | `https://energy.raunet.eu` |

   **Passwörter generieren** (auf der VM):
   ```bash
   # Für POSTGRES_PASSWORD:
   openssl rand -base64 32

   # Für SECRET_KEY:
   openssl rand -hex 32
   ```

7. **Deploy the stack** klicken

## Schritt 5: Nginx Proxy Manager konfigurieren

1. **NPM öffnen**: http://192.168.1.3:81

2. **Hosts → Proxy Hosts → Add Proxy Host**

3. **Details Tab:**
   - Domain Names: `energy.raunet.eu`
   - Scheme: `http`
   - Forward Hostname / IP: `eedc-community-api`
   - Forward Port: `8080`
   - ☑ Websockets Support

4. **SSL Tab:**
   - SSL Certificate: Request a new SSL Certificate
   - ☑ Force SSL
   - ☑ HTTP/2 Support
   - Email: deine@email.de

5. **Save**

## Schritt 6: DNS konfigurieren

Bei deinem Domain-Provider einen A-Record erstellen:

```
energy.raunet.eu  →  <öffentliche IP deines Servers>
```

## Schritt 7: Testen

```bash
# Health-Check
curl https://energy.raunet.eu/api/health

# Sollte zurückgeben:
# {"status":"ok","version":"current"}
```

Oder im Browser: https://energy.raunet.eu

---

## Wartung

### Logs anzeigen
In Portainer: Containers → eedc-community-api → Logs

Oder via SSH:
```bash
docker logs -f eedc-community-api
```

### Stack aktualisieren

1. Neues Image bauen:
   ```bash
   cd /opt/eedc-community
   git pull  # falls aus Git
   cd frontend && npm run build && cd ..
   docker build -t eedc-community-api:latest ./backend
   ```

2. In Portainer: Stacks → eedc-community → **Redeploy**

### Datenbank-Backup

```bash
docker exec eedc-community-db pg_dump -U eedc eedc_community > backup_$(date +%Y%m%d).sql
```

### Datenbank wiederherstellen

```bash
cat backup.sql | docker exec -i eedc-community-db psql -U eedc eedc_community
```
