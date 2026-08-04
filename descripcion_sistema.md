# Descripción del sistema

## ¿Qué es este proyecto?

Este proyecto es un sistema web para la gestión de una institución educativa. Permite administrar información de alumnos, matrículas, pagos, usuarios, eventos y publicaciones de marketing, todo desde una sola plataforma.

## Objetivo principal

Centralizar la operación diaria de la institución para:

- registrar y mantener datos de alumnos y apoderados,
- gestionar matrículas por ciclo, turno y horario,
- controlar pagos y cobros,
- enviar notificaciones y recordatorios por WhatsApp,
- organizar campañas y publicaciones de marketing.

## Módulos principales

### 1. Gestión de alumnos
Permite registrar información como:

- nombres completos,
- DNI,
- grado de estudios,
- sexo,
- teléfono y WhatsApp,
- fecha de nacimiento,
- colegio de procedencia,
- fotos del alumno,
- estado activo o inactivo.

También permite asociar un apoderado a uno o varios alumnos.

### 2. Gestión de apoderados
Permite administrar a los responsables del alumno, incluyendo:

- nombre completo,
- DNI,
- celular,
- dirección,
- parentesco,
- alumnos asignados.

### 3. Matrículas
Es uno de los módulos más importantes. Permite:

- registrar una matrícula para un alumno,
- asignar ciclo, turno y horario,
- definir modalidad y tipo de matrícula,
- ver el estado de la matrícula,
- generar constancias o fichas en PDF,
- enviar información por WhatsApp.

### 4. Cobranza y pagos
Permite llevar el control financiero de cada matrícula mediante:

- cuotas,
- pagos registrados,
- fechas de vencimiento,
- estado de pago,
- reportes financieros,
- seguimiento de deudas y recordatorios.

### 5. Configuración académica
Permite definir y administrar los elementos base del funcionamiento académico:

- ciclos,
- turnos,
- horarios.

Esto ayuda a organizar correctamente la oferta educativa y la asignación de estudiantes.

### 6. Usuarios y permisos
Incluye administración de usuarios del sistema, con diferentes tipos de perfiles. Esto permite controlar quién puede ver o modificar información sensible.

### 7. Notificaciones y WhatsApp
El sistema incluye funcionalidades para:

- registrar tokens de Firebase para notificaciones push,
- enviar recordatorios,
- notificar eventos relacionados con cobros o matrículas,
- enviar fichas de matrícula por WhatsApp.

### 8. Marketing
El módulo de marketing sirve para:

- crear eventos,
- subir fotos de eventos,
- publicar contenidos,
- preparar copys para redes sociales,
- subir archivos y recursos,
- gestionar publicaciones para difusión.

## Arquitectura técnica

El proyecto está desarrollado con Django y sigue una estructura modular:

- appPrincipal: configuración principal del proyecto,
- matriculas: lógica de gestión académica y financiera,
- marketing: gestión de eventos y contenidos promocionales.

## Tecnologías utilizadas

- Python
- Django
- MySQL
- HTML / CSS / JavaScript en las plantillas
- Firebase para notificaciones
- Docker para el entorno de ejecución

## Flujo general de uso

1. Se registra un alumno.
2. Se asigna un apoderado.
3. Se crea una matrícula.
4. Se define el ciclo, turno y horario.
5. Se registran los pagos o cuotas.
6. Se pueden enviar notificaciones o recordatorios.
7. El área de marketing puede crear eventos y publicaciones relacionadas.

## Despliegue del sistema

El proyecto está preparado para desplegarse con Docker y Nginx, usando la configuración definida en los archivos de entorno y contenedores del repositorio.

### Pasos básicos de despliegue

1. Ajustar las variables de entorno en el archivo de Docker Compose, especialmente:
   - `SECRET_KEY`
   - `DB_NAME`
   - `DB_USER`
   - `DB_PASSWORD`
   - `DB_HOST`

2. Crear la red Docker necesaria:

```bash
docker network create backend
```

3. Construir y levantar los servicios:

```bash
docker compose up -d --build
```

4. Aplicar las migraciones de la base de datos:

```bash
docker compose exec web python manage.py migrate
```

5. Crear un superusuario para ingresar al panel administrativo:

```bash
docker compose exec web python manage.py createsuperuser
```
No olvidar registrar el superuser

6. Recolectar archivos estáticos:

```bash
docker compose exec web python manage.py collectstatic --noinput
```

7. Acceder a la aplicación desde el puerto configurado, por ejemplo:

```bash
http://localhost:8002
```

### Recomendaciones de producción

- Cambiar la `SECRET_KEY` por una clave segura.
- Usar `DEBUG=0` en producción.
- Configurar correctamente `ALLOWED_HOSTS`.
- Asegurar la base de datos MySQL y sus credenciales.
- Mantener los directorios de media y estáticos con permisos adecuados.

## Explicación sencilla para un usuario no técnico

Este sistema sirve para organizar la gestión de una academia o institución educativa sin usar papeles ni hojas dispersas. Permite registrar alumnos, asignar apoderados, crear matrículas, controlar pagos, enviar recordatorios y publicar información o eventos para la comunidad.

En términos simples, es una herramienta de control diario que ayuda a la institución a mantener orden en la parte académica, financiera y comunicacional.

## Explicación técnica del código

El proyecto está desarrollado en Django, un framework de Python para aplicaciones web. La lógica principal está separada en aplicaciones modulares: una para matrículas y otra para marketing. Cada módulo usa modelos para representar datos, vistas para procesar solicitudes y plantillas para mostrar la interfaz.

La arquitectura sigue un patrón clásico MVC/MVT, donde:

- los modelos definen la estructura de los datos,
- las vistas manejan la lógica del negocio,
- las URLs enlazan las solicitudes a las funciones correctas,
- los formularios validan y capturan información del usuario.

## Mapa de módulos y funciones del proyecto

### App principal
- Configura el proyecto Django.
- Define la base de datos, rutas globales, archivos estáticos y media.

### App de matrículas
- Gestiona alumnos, apoderados, matrículas, pagos, ciclos, turnos y horarios.
- Incluye funciones para generar constancias, fichas PDF y enviar mensajes por WhatsApp.
- También maneja usuarios, permisos y reportes financieros.

### App de marketing
- Administra eventos, fotos, publicaciones y recursos de comunicación.
- Permite construir campañas promocionales y organizar contenidos para redes o difusión institucional.

## Resumen

Este sistema funciona como una plataforma integral para administrar una academia o institución educativa, combinando gestión académica, financiera, comunicacional y promocional en un solo entorno.
