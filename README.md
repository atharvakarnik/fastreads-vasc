# VascReads

VascReads is a lightweight, local NIfTI viewer for reviewing structural MRI images in a web browser. Wave 1 supports one T1, T2, and FLAIR image per participant and keeps the source images, notes, and review data on the local computer.

The viewer uses vanilla HTML/CSS/JavaScript, the vendored NiiVue build, and a Python standard-library HTTP server. It has no build step or runtime network dependency. It has not been clinically or diagnostically validated.

## Requirements

- Python 3.10 or newer
- A modern browser with WebGL support

No Python packages, npm packages, or frontend build tools are required.

## Data layout

Place each participant in an immediate subdirectory of `data/`. The directory name is the participant ID, and filenames must match that ID exactly:

```text
data/
├── <ID_1>/
│   ├── <ID_1>_T1.nii[.gz]
│   ├── <ID_1>_T2.nii[.gz]
│   └── <ID_1>_FLAIR.nii[.gz]
└── <ID_2>/
    ├── <ID_2>_T1.nii[.gz]
    ├── <ID_2>_T2.nii[.gz]
    └── <ID_2>_FLAIR.nii[.gz]
```

Only these explicit Wave 1 filenames are recognized, using either `.nii` or `.nii.gz`. If both forms are present for one modality, the uncompressed `.nii` file is used. A participant needs at least one of the three files. If a modality is missing, the participant remains available and only that modality control is disabled. Participant IDs are naturally sorted.

Do not add medical images to Git. The entire `data/` directory is intentionally ignored.

## Run the viewer

From the repository directory, run:

```bash
python server.py
```

Then open [http://127.0.0.1:8000/viewer.html](http://127.0.0.1:8000/viewer.html). The server binds only to localhost.

### Windows

Double-click `Start_Viewer.bat`. Keep the **VascReads Server** window open while using the viewer. `Stop_Viewer.bat` explains how to stop it.

### macOS and Linux

Run:

```bash
bash Start_Viewer.sh
```

On macOS, `Start_Viewer.command` can also be opened directly. Keep its Terminal window open while using the viewer and press Ctrl+C when finished.

## Review and notes

Notes and the existing Wave 1 review fields are participant-specific. Changes autosave in browser-local storage under VascReads-specific keys. The **Save Notes → notes.csv** button explicitly writes the current local review collection to `notes.csv`, and saved reads can be skipped during Previous/Next navigation.

`notes.csv` contains local physician review data and is intentionally ignored by Git, along with medical imaging data. Do not upload or commit either.

## Wave 1 scope

The viewer displays one structural image at a time and provides T1, T2, and FLAIR selection, orthogonal navigation, independent per-pane zoom/reset, crosshair visibility, and linked Min/Max plus Window/Level controls. Intensity adjustments are kept separate for each participant and modality while that participant is active.

Image overlays and segmentation masks are not implemented yet.
