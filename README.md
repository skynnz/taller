# Documentación de la Aplicación

## Funcionalidades Actuales

### 1. Autenticación de Usuarios

- **Registro de Usuarios**: Los nuevos usuarios pueden crear una cuenta proporcionando un nombre de usuario y contraseña.
- **Inicio de Sesión**: Los usuarios registrados pueden iniciar sesión en la aplicación.
- **Cierre de Sesión**: Los usuarios pueden cerrar sesión de forma segura.

### 2. Gestión de Sesiones

- Mantenimiento de la sesión del usuario a través de diferentes páginas.
- Protección de rutas que requieren autenticación.

### 3. Interfaz de Usuario

- **Plantilla Base**: Utiliza AdminLTE 3 para una interfaz de usuario moderna y responsive.
- **Página de Registro**: Formulario para crear nuevas cuentas de usuario.
- **Página de Inicio de Sesión**: Interfaz para que los usuarios accedan a sus cuentas.
- **Dashboard**: Página principal para usuarios autenticados.

### 4. Seguridad

- Almacenamiento seguro de contraseñas mediante hash.
- Protección contra inyección SQL utilizando consultas parametrizadas.

### 5. Base de Datos

- Integración con PostgreSQL para almacenar información de usuarios.

### 6. Estructura del Proyecto

- Organización modular del código (blueprints de Flask).
- Separación de lógica de autenticación en un módulo dedicado.

### 7. Manejo de Errores

- Mensajes de error personalizados para problemas de autenticación.

## Tecnologías Utilizadas

- Flask: Framework web de Python
- PostgreSQL: Sistema de gestión de bases de datos
- AdminLTE 3: Plantilla de panel de administración
- Werkzeug: Utilidades web para Python, incluida la gestión de seguridad de contraseñas

## Próximos Pasos

- Implementar recuperación de contraseña
- Añadir más funcionalidades al dashboard
- Mejorar la gestión de perfiles de usuario

## TreeView del Proyecto

app/
├── models/
│ ├── init.py
│ ├── user.py (Modelo de Usuario)
│ └── roles.py (Definición de roles y permisos)
├── templates/
│ ├── base.html (Plantilla base)
│ └── auth/
│ └── login.html (Plantilla de inicio de sesión)
├── static/
│ ├── css/
│ │ └── adminlte.min.css
│ └── dist/
│ └── img/
│ └── user2-160x160.jpg
├── utils/
│ └── decorators.py (Decoradores para control de acceso)
├── views/
│ └── admin.py (Rutas para el panel de administración)
├── init.py (Configuración de la aplicación Flask)
└── auth.py (Rutas de autenticación)


utils
https://recursospython.com/guias-y-manuales/crear-documentos-pdf-en-python-con-reportlab/