## 1. Estructura por capas

```
intelligent-library-search-system/
├── aplicacion.py                   # lanza la interfaz de escritorio
├── servidor.py                     # lanza un nodo:  --nodo 1|2|3
├── .env                            # sube desde backend/
├── requirements.txt
│
├── entidades/                      # ◄ CAPA DE ENTIDAD
│   ├── __init__.py
│   └── entidades.py
│
├── datos/                          # ◄ CAPA DE DATOS
│   ├── __init__.py
│   ├── conexion.py
│   └── repositorios/
│       ├── __init__.py
│       ├── repositorio_base.py
│       ├── repositorio_biblioteca.py
│       ├── repositorio_libro.py
│       ├── repositorio_usuario.py
│       ├── repositorio_ejemplar.py
│       ├── repositorio_prestamo.py
│       └── repositorio_consulta.py
│
├── negocio/                        # ◄ CAPA DE NEGOCIO
│   ├── __init__.py
│   ├── excepciones.py
│   ├── servicio_catalogo.py
│   ├── servicio_prestamo.py
│   └── servicio_ia.py
│
├── presentacion/                   # ◄ CAPA DE PRESENTACIÓN
│   ├── __init__.py
│   ├── servicios/                  # fachada gRPC del nodo
│   │   ├── __init__.py
│   │   ├── servicio_grpc.py
│   │   ├── servidor_grpc.py
│   │   ├── cliente_grpc.py
│   │   ├── contrato/
│   │   │   └── biblioteca.proto
│   │   └── generados/
│   └── escritorio/                 # interfaz Tkinter
│       ├── __init__.py
│       ├── estilos.py
│       ├── componentes.py
│       ├── servicio_cliente.py
│       └── vistas/
│
├── configuracion/                  # transversal
│   ├── __init__.py
│   └── ajustes.py
│
├── herramientas/                   # scripts de apoyo
│   ├── cargar_datos.py
│   ├── diagnostico.py
│   ├── generar_protos.py
│   ├── probar_flujo.py
│   └── probar_nodos.py
│
└── docs/
```