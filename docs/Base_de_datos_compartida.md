# Trabajar entre varios equipos

Cada integrante tiene su propia instancia de SQL Server en su computador. Eso
funciona bien para desarrollar, pero crea una confusión: aunque los tres tengan
el mismo código, cada uno ve datos distintos. Un libro que uno registra no
aparece en la pantalla del otro.

Este documento explica las tres formas de resolverlo, de la más simple a la más
parecida al escenario real del proyecto.

---

## Primero: entender qué se comparte y qué no

El sistema **no replica datos entre bibliotecas**, y eso es a propósito. Cada
nodo manda sobre su propia base de datos y la disponibilidad global se arma
preguntándoles a los tres en el momento de la consulta.

Eso significa que hay dos cosas distintas que se pueden compartir:

| Qué se comparte | Para qué sirve |
|---|---|
| **Los servidores de nodo** | Que los tres vean el mismo inventario de las tres sedes. Es lo que corresponde al diseño del proyecto. |
| **Las bases de datos** | Que los tres trabajen contra los mismos datos. Es cómodo para desarrollar, pero se aleja del escenario distribuido. |

La opción A comparte los servidores. Las opciones B y C comparten las bases.

---

## Opción A — Cada uno levanta su nodo y se conectan entre sí

Es la que mejor representa el proyecto: tres bibliotecas, tres equipos, tres
bases de datos independientes.

**Cómo funciona.** Cada integrante levanta un nodo distinto en su máquina
(`python servidor.py --nodo 1`, el segundo `--nodo 2`, el tercero `--nodo 3`), y
los tres configuran su `.env` apuntando a las direcciones IP de los otros dos.

```env
NODO1_HOST=192.168.1.10
NODO1_PORT=50051

NODO2_HOST=192.168.1.11
NODO2_PORT=50052

NODO3_HOST=192.168.1.12
NODO3_PORT=50053
```

**Requisitos.** Los tres equipos tienen que verse por red. En la misma red local
(el salón, la casa de alguno) funciona directamente, siempre que cada uno abra
el puerto correspondiente en el Firewall de Windows:

```powershell
New-NetFirewallRule -DisplayName "Nodo biblioteca" -Direction Inbound `
  -Protocol TCP -LocalPort 50051 -Action Allow
```

**Desde casas distintas** no funciona sin más, porque las IP domésticas están
detrás de un router. Hay dos salidas: una VPN entre los tres equipos, o un túnel
que publique el puerto en internet. Para una sustentación, la VPN es más estable.

**Ventaja.** Es el escenario real del proyecto y permite demostrar de verdad la
tolerancia a fallos: alguien apaga su nodo y los otros dos siguen respondiendo.

**Desventaja.** Depende de que los tres equipos estén encendidos a la vez.

---

## Opción B — Una sola máquina con las tres bases de datos

La más simple de todas y la que conviene para avanzar en el desarrollo.

Un integrante instala SQL Server, crea las tres bases de datos y levanta los
tres nodos en su equipo. Los otros dos configuran su `.env` apuntando a esa
máquina:

```env
DB_SERVER=192.168.1.10\SQLEXPRESS
DB_TRUSTED_CONNECTION=false
DB_USER=biblioteca
DB_PASSWORD=la-que-definan

NODO1_HOST=192.168.1.10
NODO2_HOST=192.168.1.10
NODO3_HOST=192.168.1.10
```

Hay que habilitar en esa máquina la autenticación de SQL Server, crear un
usuario con permisos sobre las tres bases y activar el protocolo TCP/IP en el
Administrador de configuración de SQL Server, que viene desactivado por defecto
en las instalaciones Express.

**Ventaja.** Se configura en media hora y los tres ven lo mismo.

**Desventaja.** Si esa máquina se apaga, nadie trabaja. Y las tres bases viven
en el mismo motor, que no es exactamente el escenario distribuido.

---

## Opción C — Las bases de datos en la nube

Sirve cuando los tres trabajan desde casas distintas y a horas distintas.

Se crean tres bases de datos en un servicio administrado de SQL Server en la
nube. Varios proveedores tienen un nivel gratuito suficiente para un proyecto
académico, con la base suspendiéndose cuando nadie la usa.

La configuración es la misma de la opción B, cambiando el servidor:

```env
DB_SERVER=nombre-del-servidor.database.windows.net
DB_TRUSTED_CONNECTION=false
DB_USER=usuario
DB_PASSWORD=contrasena
DB_ENCRYPT=true
DB_TRUST_SERVER_CERTIFICATE=false
```

Dos advertencias prácticas. La primera es que hay que autorizar la dirección IP
de cada integrante en el cortafuegos del servicio, y las IP domésticas cambian:
toca volver a autorizarlas cada tanto. La segunda es que, si la base estuvo
suspendida, la primera conexión tarda y el sistema puede reportar el nodo como
caído; conviene abrir la aplicación un minuto antes de empezar a trabajar.

**Ventaja.** Funciona desde cualquier lugar y a cualquier hora, sin depender de
que un compañero tenga el computador encendido.

**Desventaja.** Requiere crear cuentas y configurar cortafuegos, y la latencia
es mayor que en red local.

---

## Recomendación

Para el día a día, la **opción B**: es la más rápida de montar y evita la
confusión de ver datos distintos.

Para la sustentación, la **opción A**: es la que permite mostrar lo que el
proyecto realmente propone, incluido el momento en que se apaga un nodo y el
sistema sigue respondiendo con los otros dos.

En cualquiera de las tres, el `.env` **nunca se sube al repositorio**. Cada
integrante parte de `.env.example` y pone sus propios valores.
