# 📦 Instrucciones de Empaquetado - Rotoscopia

## Método Automático (Recomendado)

1. **Ejecutá el script de build:**
   ```bash
   python build.py
   ```

2. **El .exe estará en:**
   ```
   dist/Rotoscopia.exe
   ```

---

## Método Manual (PyInstaller)

### 1. Instalar PyInstaller
```bash
pip install pyinstaller
```

### 2. Empaquetar
```bash
pyinstaller --name=Rotoscopia --onefile --windowed --clean rotoscopia/main.py
```

### 3. Encontrar el ejecutable
```
dist/Rotoscopia.exe
```

---

## Opciones de Empaquetado

### Un solo archivo (.exe)
```bash
pyinstaller --onefile --windowed rotoscopia/main.py
```

### Carpeta con DLLs (más rápido de iniciar)
```bash
pyinstaller --windowed rotoscopia/main.py
```

### Con icono personalizado
```bash
pyinstaller --onefile --windowed --icon=icon.ico rotoscopia/main.py
```

---

## Dependencias Necesarias

Todas las dependencias en `requirements.txt`:
- PySide6 (Qt GUI)
- opencv-python (Procesamiento de imagen/video)
- numpy (Arrays)
- Pillow (Manejo de imágenes)

---

## Problemas Comunes

### "No module named cv2"
PyInstaller a veces no detecta OpenCV automáticamente:
```bash
pyinstaller --onefile --windowed --hidden-import=cv2 rotoscopia/main.py
```

### El .exe es muy grande
Normal con PySide6 (~150-200 MB). Para reducir:
- Usar `--onedir` en vez de `--onefile`
- Eliminar imports no usados

### No arranca / Pantalla negra
Ejecutar sin `--windowed` para ver errores:
```bash
pyinstaller --onefile rotoscopia/main.py
```

---

## Estructura después del build

```
Rotoscopia/
├── rotoscopia/          # Código fuente
├── build/               # Archivos temporales (se puede borrar)
├── dist/                # ✅ EJECUTABLE AQUÍ
│   └── Rotoscopia.exe
└── Rotoscopia.spec      # Configuración de PyInstaller
```
