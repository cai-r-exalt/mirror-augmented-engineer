# La Buvette de Bel'Air : construyendo un backend para la famosa buvette del festival eXalt. Con Python, IA y amor.

Versión inglesa : [README.md](README.md)  
Versión francesa : [README_fr.md](README_fr.md)

>[!note]
> 
> Este proyecto forma parte del camino de aprendizaje eXalt IT augmented engineer, ubicado en su [academy](https://academy.exalt-company.com/paths/699c49f3a1dffef24c46c739/home).

Hola y bienvenido al repositorio del proyecto La Buvette de Bel'Air!

Este proyecto es tu terreno de juego para crear un backend robusto de gestión de bebidas y snacks.

Vas a construir el mejor backend posible usando Python.

Pero, lo más importante, tu nuevo mejor amigo: GitHub Copilot, tu pato de goma / becario demasiado entusiasta para el pair programming!

## Estructura del proyecto

```
augmented-engineer-python-starter/
 application/      # Punto de entrada — conecta el dominio y la infraestructura
 domain/           # Lógica de negocio y modelo de dominio
 infrastructure/   # Adaptadores, persistencia, integraciones externas
```

## Instalación de la cadena de herramientas

| Herramienta | Versión | Documentación |
|-------------|---------|---------------|
| Python | 3.13+ | [python.org](https://www.python.org/downloads/) |
| uv | latest | [docs.astral.sh/uv](https://docs.astral.sh/uv/) |
| Git | latest | [git-scm.com](https://git-scm.com/downloads) |

> Instala uv mediante `pip install uv` o el [script de instalación oficial](https://docs.astral.sh/uv/getting-started/installation/).

## Cómo empezar

### Requisitos previos

- Python 3.13+
- uv
- Git

### Fork & Clone

Haz fork de este repositorio en tu propia cuenta de Gitlab (solo rama main) y luego clónalo:

```bash
git clone <URL_DE_TU_FORK>
cd augmented-engineer-python-starter
```

### Espejar en GitHub

Para poder usar correctamente las funcionalidades de IA avanzadas con Copilot, espeja este repositorio en tu cuenta GitHub:

```bash
git remote add github <the URL of your new GitHub repository>
git branch -M main
git push -u github main
```

### Instalar las dependencias

```bash
uv sync
```

### Ejecutar los tests

```bash
uv run pytest
```

### Ejecutar la aplicación

```bash
uv run python -m application.main
```

## Próximos pasos

Comienza siguiendo el material de formación en la [academy](https://academy.exalt-company.com/paths/699c49f3a1dffef24c46c739/home).

Consulta [FEATURES_es.md](./FEATURES_es.md) para la lista completa de historias de usuario y criterios de aceptación.

Feliz programación!
