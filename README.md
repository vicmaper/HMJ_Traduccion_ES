# Soushuu Senshinkan Gakuen: Hachimyoujin — traducción al español

Kit para jugar **Soushuu Senshinkan Gakuen: Hachimyoujin** (light, 2017, motor MALIE) en español latinoamericano neutro,
o para hacer y corregir tu propia traducción en un CSV.

**Dudas y reportes:** Discord <https://discord.gg/XJmNBWcP9>

## Qué hace
- Saca el guion de **tu** copia del juego a un CSV (`id, voice, japanese, spanish, status`) que se edita en Excel o LibreOffice.
- Revisa y corrige solo lo seguro (marcas `{v:}{/v}{end}{u000A}`, puntuación japonesa, `«…»`, `¡¿`, espacios),
  pone los saltos de renglón por píxeles y avisa lo que no cabe (máximo 16 renglones).
- Genera `data3.dat` (el juego lo carga encima de `data1.dat`) con:
  guion, nombres del historial, opciones de elección, interfaz, fuente adaptada y videos de estado en español.
- Crea `malie_es.exe` (menús de Windows y avisos en español) a partir de tu `malie.exe`.
- Exporta tu traducción **sin japonés** para compartirla.

## Edición compatible
| | |
|---|---|
| Juego | Soushuu Senshinkan Gakuen: Hachimyoujin, light, 2017 (PC, disco) |
| `malie.exe` | v1.1.0.0 (2017-09-07), md5 `e45c0a09fb19f64d0ca5fc98bd4b5e47` |
| `exec.dat` (en `data1.dat`) | md5 `bd677ce6ee9cb688838fce05166ad69d` |
| Clave de los `.dat` | `Soushuu Senshinkan Gakuen Hachimyoujin` (align 0x400) |

Sin parches oficiales. Si tu copia es otra, el kit se detiene sin cambiar nada: pide ayuda en el Discord.

## Uso rápido
1. Descarga `HMJ_Traduccion_ES.zip` de **Releases** y descomprímelo fuera de la carpeta del juego.
2. Abre `HMJ_Kit.exe`, elige la carpeta del juego y pulsa **1 → 3 → 4**.
3. Juega con `malie_es.exe`.

Guía completa: [GUIA_PARA_FANS.txt](GUIA_PARA_FANS.txt).

Con Python 3.10+: `pip install -r requirements.txt` y `python herramientas/hmj_gui.py`
(o `python herramientas/hmj_kit.py extraer|revisar|validar|generar|exe|compartir|dividir`).

## Qué NO trae este repositorio
- Ningún archivo del juego, ni imágenes, ni videos, ni la fuente, ni el texto japonés.
  La interfaz, la fuente y los videos en español se **rehacen en tu computadora** a partir de tu copia.
- `traduccion/HMJ_es.csv` y `traduccion/cadenas_es.tsv` llevan **solo el español** (por id/offset).
- `herramientas/hmj_exe_parche.json` lleva solo los bytes que cambian (texto en español) para `malie_es.exe`.

No subas aquí el CSV de trabajo, la carpeta `trabajo/` ni ningún `.dat`: llevan el texto y los archivos del juego
(`.gitignore` ya los excluye).

## Cómo se arma el .exe
Al publicar una versión (Releases → *Draft a new release*), GitHub Actions (`.github/workflows/construir-exe.yml`)
arma `HMJ_Kit.exe` con PyInstaller 6.10 y sube `HMJ_Traduccion_ES.zip` a esa versión.
También se puede lanzar a mano en Actions → *Construir HMJ_Kit.exe* → *Run workflow*.

## Créditos
Traducción y herramientas: proyecto de traducción HMJ (ver Discord). Basado en herramientas MALIE de los proyectos
Kajiri Kamui Kagura y Paradise Lost. Claves de cifrado MALIE tomadas de GARbro.
Proyecto de fans sin fines de lucro; compra el juego original.
