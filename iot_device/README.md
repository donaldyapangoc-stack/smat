# iot_device – Emulador de Hardware IoT  emula el comportamiento de un microcontrolador  que toma lecturas de un sensor de nivel de río y las envía automáticamente a la API SMAT mediante HTTP + JWT.

---

## ¿Cómo funciona la comunicación

```
[Sensor físico / Script Python]
         │  lectura (float)
         ▼
leer_sensor_emulado()
         │
         ▼
POST /lecturas/
Headers: { Authorization: "Bearer <JWT>" }
Body:    { "valor": 42.3, "estacion_id": 1 }
         │
         ▼
[FastAPI SMAT – valida JWT → guarda en SQLite]
         │
         ▼
[App Flutter – refresca lista de lecturas]
```

### Token JWT
1. Obtener el token haciendo login en el backend:
   ```bash
   curl -X POST http://localhost:8000/token \
        -d "username=admin&password=admin"
   ```
2. Copiar el valor de `access_token` y pegarlo en la variable `TOKEN` de
   `sensor_emitter.py`.

El token viaja dentro del encabezado 
`Authorization: Bearer <token>`. El servidor verifica la firma del JWT antes de
aceptar la lectura, garantizando que solo dispositivos autorizados puedan
escribir datos.

