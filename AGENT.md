# fastreads-vasc — Codex project instructions

You are working with three sibling Git repositories:

1. `../fastreads` — read-only canonical implementation reference.
2. `../fastreads-jcb` — read-only secondary reference. This is a different DICOM-oriented adaptation and is not the implementation baseline for this project.
3. `fastreads-vasc` — the current repository and the only repository you may modify.

You are currently working inside `fastreads-vasc`.

Never modify `../fastreads` or `../fastreads-jcb`.

Do not commit, delete, rename, or otherwise alter files in either sibling repository.

## Project goal

`fastreads-vasc` is a small local physician-facing NIfTI review viewer derived directly from `fastreads`.

The first development wave must support three structural MRI modalities for each participant:

* T1
* T2
* FLAIR

This is a NIfTI viewer.

Do not convert this project to DICOM.

Do not introduce `@niivue/dicom-loader`.

Do not introduce Vite, npm, React, Vue, Angular, TypeScript, or another frontend framework.

Keep the same lightweight architecture as `fastreads`:

* vanilla HTML/CSS/JavaScript
* the existing vendored `niivue.umd.js`
* Python standard-library backend
* local HTTP server
* no build step
* no external service
* no runtime network dependency

The goal of this first wave is an adaptation, not a rewrite.

## Reference hierarchy

Before editing code, inspect at minimum:

```text
../fastreads/server.py
../fastreads/viewer.html
../fastreads/Start_Viewer.bat
../fastreads/Start_Viewer.sh
../fastreads/Start_Viewer.command
```

The copied versions already present in `fastreads-vasc` are the starting implementation.

When behavior is ambiguous, prefer preserving the working `fastreads` implementation unless these instructions explicitly require a change.

In particular, preserve rather than reinvent the existing implementation for:

* NiiVue initialization
* axial/coronal/sagittal slice navigation
* per-pane zoom selection
* per-pane reset zoom
* zoom coordinate calculations
* crosshair visibility
* canvas/tool-overlay behavior
* responsive redraw/resizing
* image intensity-range detection
* Min/Max controls
* Window/Level conversion logic
* linked Window and Level sliders/numeric inputs
* fixed slider bounds during interaction
* Auto/reset intensity behavior
* subject Previous/Next navigation
* Go to participant ID
* Go to participant index
* status/error messages
* local note autosave
* explicit notes CSV persistence
* saved-read tracking

Do not simplify these working mechanisms merely because a shorter implementation is possible.

`../fastreads-jcb` may be inspected for general repository-safety ideas or launcher practices, but do not copy its DICOM/Vite architecture into this application.

## Repository layout

Keep the repository small.

The intended first-wave structure is approximately:

```text
fastreads-vasc/
├── AGENTS.md
├── .gitignore
├── README.md
├── data/
├── niivue.umd.js
├── server.py
├── viewer.html
├── Start_Viewer.bat
├── Start_Viewer.sh
├── Start_Viewer.command
└── Stop_Viewer.bat
```

`data/` is local and ignored by Git.

Do not create additional source files merely to reorganize code.

Do not split `viewer.html` into a framework or multi-file frontend unless the user explicitly requests that later.

Treat `niivue.umd.js` as vendored reference code. Do not modify it unless the user explicitly requests a NiiVue-library change.

## Local imaging data layout

Use a fixed data root relative to `server.py`:

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
```

Participant data will be arranged as:

```text
fastreads-vasc/
└── data/
    ├── <ID_1>/
    │   ├── <ID_1>_T1.nii.gz
    │   ├── <ID_1>_T2.nii.gz
    │   └── <ID_1>_FLAIR.nii.gz
    ├── <ID_2>/
    │   ├── <ID_2>_T1.nii.gz
    │   ├── <ID_2>_T2.nii.gz
    │   └── <ID_2>_FLAIR.nii.gz
    └── ...
```

The participant directory name is the canonical participant ID.

For participant `<ID>`, recognize these first-wave filenames:

```text
<ID>_T1.nii.gz
<ID>_T2.nii.gz
<ID>_FLAIR.nii.gz
```

Do not invent alternate modality-detection heuristics in this first wave.

Do not inspect NIfTI headers to guess whether a file is T1, T2, or FLAIR.

Use the explicit filenames.

A participant may be missing one or more modalities.

A participant with at least one valid modality must remain available.

Missing one modality must disable only that modality's tab/control; it must not remove the participant.

Do not add example medical images.

Do not automatically create participant folders.

If `data/` is absent or contains no usable participants, provide a clear status message rather than falling back to PET example data.

## Backend subject discovery

Replace the PET/MNI-specific discovery logic in `server.py`.

`GET /api/subjects` should discover the immediate participant directories in `data/`, identify the three expected NIfTI files, and return naturally sorted IDs.

A suitable response is:

```json
{
  "subjects": [
    {
      "id": "012345",
      "t1_path": "data/012345/012345_T1.nii.gz",
      "t2_path": "data/012345/012345_T2.nii.gz",
      "flair_path": "data/012345/012345_FLAIR.nii.gz"
    }
  ]
}
```

A missing modality should be returned as `null`.

Do not accept arbitrary filesystem paths from the browser.

Only return paths discovered underneath `DATA_DIR`.

Use participant directory names as IDs.

Sort participant IDs naturally rather than assuming that every future ID must be an integer.

Keep the HTTP server bound only to:

```text
127.0.0.1
```

Do not expose it on `0.0.0.0`.

## Three image views

Replace the PET/MNI view selector with exactly three first-wave modality views:

```text
T1
T2
FLAIR
```

Use the existing view-selection concept rather than introducing multiple simultaneous viewers.

Display one base NIfTI volume at a time.

On startup:

1. Prefer T1 if the first participant has T1.
2. Otherwise choose T2 if available.
3. Otherwise choose FLAIR.

When navigating between participants, attempt to keep the currently selected modality.

If that modality is unavailable for the new participant, fall back in this order:

```text
T1 -> T2 -> FLAIR
```

Disable unavailable modality controls.

Do not display an error merely because one of the other modalities is missing.

Update generic UI labels appropriately:

* `View` should show T1, T2, or FLAIR.
* `Source` should show the current NIfTI filename.
* Remove the MNI-template chip.
* Remove PET/MNI terminology.
* Remove Centiloid display.
* Remove atlas/VOI controls.
* Remove PET opacity controls.
* Remove MNI template opacity controls.
* Remove PET-specific grayscale inversion behavior unless explicitly requested later.

Structural images should use normal grayscale display.

## Image loading

Continue using the existing vendored NiiVue UMD build and `NVImage.loadFromUrl`.

Do not introduce another NIfTI-reading library.

For each participant/modality:

1. Obtain the path from `/api/subjects`.
2. Load the selected NIfTI.
3. Clear/rebuild the NiiVue volume list appropriately.
4. Add the structural image as base volume index `0`.
5. Apply normal grayscale.
6. initialize that image's intensity controls.
7. restore that modality's zoom state if applicable.
8. redraw the viewer.

Guard asynchronous loading so that rapidly changing participant or modality cannot allow an older completed request to replace the newly selected image.

Do not cache every decoded image indefinitely if doing so would cause unbounded browser memory growth.

A small current/recent image cache is acceptable, but do not redesign the entire application merely to introduce caching.

## Viewer toolbox — preserve carefully

The existing `fastreads` custom toolbox is important and must remain functionally equivalent.

Retain:

* Navigate
* Zoom
* Reset Zoom
* Crosshair

Retain the per-plane behavior for:

* axial
* coronal
* sagittal

Do not replace the custom zoom logic with a generic whole-canvas zoom.

The current implementation intentionally keeps independent pan/zoom state for orthogonal panes.

Extend the existing view-state mapping from PET/MNI to:

```text
T1
T2
FLAIR
```

Participant changes should reset participant-specific zoom state as the existing viewer does.

Changing modality within one participant may keep independent zoom state for each modality.

Preserve responsive canvas resizing and the transparent tool-overlay canvas.

## Intensity, brightness and contrast controls

The existing Min/Max plus Window/Level behavior is the required brightness/contrast system.

Do not replace it with a gamma-only brightness slider.

Rename PET-specific variables/UI labels to generic image/intensity terminology where practical.

For the active structural image retain:

```text
Intensity range
  Min
  Max
  Auto

Window
  slider
  numeric value

Level
  slider
  numeric value
```

Preserve the existing relationships:

```text
window = max - min
level = (min + max) / 2

min = level - window / 2
max = level + window / 2
```

Preserve the existing default-range preference:

1. `cal_min` / `cal_max`
2. `robust_min` / `robust_max`
3. `global_min` / `global_max`

Preserve fixed Window/Level slider bounds while interacting with an image. Do not dynamically move slider bounds during a drag.

`Auto` must restore the original NIfTI-derived display range.

The important adaptation is state separation.

T1, T2, and FLAIR have different signal-intensity distributions.

Therefore, never share one manual Min/Max or Window/Level override between modalities.

Maintain display-range state independently for the active:

```text
participant + modality
```

For example, changing the T1 window must not alter the FLAIR display range when FLAIR is opened.

Window/Level controls must always affect the base structural volume only.

## Notes and review behavior — preserve for Wave 1

The Notes/Review subsystem will be redesigned in a later development wave.

Do not redesign its clinical fields during this first wave unless the user gives new requirements.

For now, preserve the existing behavior from `fastreads`, including where applicable:

* participant-specific notes
* local browser autosave
* explicit save to `notes.csv`
* Clear This
* Review fields
* saved-read detection
* Skip saved reads
* reload/merge behavior between browser state and `notes.csv`

Do not reinterpret the existing Review fields or add new physician-specific choices in Wave 1.

The user will provide those requirements later.

However, change browser local-storage namespaces so this application cannot collide with `fastreads` when both are accessed through `127.0.0.1:8000`.

Use VASC-specific keys such as:

```text
FASTREADS_VASC_NOTES_V1
FASTREADS_VASC_REVIEW_V1
```

Do not reuse:

```text
PET_VIEWER_NOTES_FULL_ONLY_V2
PET_VIEWER_REVIEW_FIELDS_V1
```

Keep `notes.csv` local and Git-ignored.

Do not add review data to Git.

Remove Centiloid loading and `/api/centiloids`; it is unrelated to this application.

## Overlays — NOT part of Wave 1

Do not implement overlays in the initial T1/T2/FLAIR adaptation.

Do not create placeholder overlay buttons or empty overlay controls.

The following section defines how overlays must be added if the user explicitly requests them in a later or intermediate task.

### Overlay extension contract

When the user asks to add one or more masks/overlays, first determine from that task:

* which base modality or modalities the overlay belongs to
* the exact expected overlay filename
* whether it is a binary mask or a multi-label segmentation
* the requested display color
* the requested default opacity

Do not invent these properties when they have not been specified.

The base structural NIfTI must remain volume index `0`.

Overlay volumes must be added after the base image.

Brightness/contrast Min/Max and Window/Level controls must continue to modify only base volume index `0`.

### Binary mask color

For a binary mask, preserve the successful custom-label-LUT approach from `../fastreads/viewer.html`.

Use label:

```text
0 = transparent
1 = requested mask color
```

Use one canonical hexadecimal color value as the source of truth.

For example:

```javascript
{
  key: "example_mask",
  label: "Example mask",
  color: "#e74c3c",
  defaultOpacity: 0.30
}
```

The same `color` value must control:

* the NiiVue label LUT
* the visual color shown in the UI
* the opacity slider accent color, when browser styling allows it

Do not maintain separate hardcoded colors for the image and the UI.

The displayed mask color and its UI indicator must therefore remain matched.

Reuse/adapt the existing `hexToRgb`, binary label-LUT, and `applyLabelLUTToImage` pattern from the canonical `fastreads` viewer rather than substituting an unrelated continuous colormap.

### Overlay opacity

Each overlay should have an opacity control from:

```text
0.00 to 1.00
```

A reasonable default is:

```text
0.30
```

unless the user specifies another value.

Use a small increment such as:

```text
0.05
```

Display the current numerical opacity beside the slider.

If an overlay visibility checkbox is requested, unchecked should set effective opacity to `0` without destroying the stored slider value.

Use the existing safe NiiVue opacity setter pattern.

### Mask interpolation

Label masks must use nearest-neighbor interpolation where the NiiVue API permits it.

Do not use linear interpolation for categorical labels merely to make edges look smoother.

### Multi-label masks

Do not force a multi-label segmentation into the two-entry binary LUT.

For a true multi-label image, create an explicit label LUT mapping the required integer labels to their requested colors.

Label `0` remains transparent.

Do not merge labels unless the user explicitly requests a binary union.

### Geometry

Assume overlays have already been registered/resampled to the appropriate base image unless the user explicitly requests registration functionality.

Do not silently perform browser-side spatial registration or resampling.

If an overlay is clearly incompatible with its intended base image because of dimensions/orientation/affine geometry, report the incompatibility rather than visually presenting a misleading overlay.

### Missing overlays

A missing overlay must disable or hide only that overlay control.

It must not make the participant or its base T1/T2/FLAIR image unavailable.

### Backend changes for future overlays

When an overlay is actually requested, extend `/api/subjects` with the discovered overlay path/availability using the exact filename convention specified by the user.

Do not expose arbitrary filesystem paths.

Do not scan unrelated files heuristically unless specifically requested.

## Remove inherited PET-specific behavior

The completed first-wave VASC viewer should not retain application behavior related to:

```text
PET
MNI
Centiloid
atlas templates
VOIs
PET-space
MNI-space
Cohort_Centiloids.csv
PET opacity
MNI template opacity
PET grayscale inversion
```

Do not remove generic helper code merely because it originated in the PET viewer if that helper is still necessary for the VASC viewer.

For example, the custom zoom implementation and label-LUT helpers may be retained if useful.

The goal is removal of PET-specific behavior, not arbitrary code churn.

## Launch workflow

Preserve the simple local workflow:

```bash
python server.py
```

and the existing launch scripts for their respective operating systems.

Adapt all launcher names/messages/readiness checks so they refer to FastReads VASC rather than PET Viewer.

Do not add npm installation.

Do not add a frontend build step.

Do not open an external web service.

Continue to launch:

```text
http://127.0.0.1:8000/viewer.html
```

unless the user explicitly changes the port later.

Launcher readiness checks must test for VASC-specific UI markers rather than old strings such as `petWindowSlider` or `centiloidReveal`.

## README

After the first-wave implementation works, create or rewrite `README.md` for `fastreads-vasc`.

Do not copy the PET README unchanged.

Document:

* purpose of the local viewer
* Python requirement
* launch instructions
* Windows launcher
* macOS/Linux launcher
* required `data/<ID>/` layout
* exact T1/T2/FLAIR filenames
* missing-modality behavior
* local notes behavior
* statement that medical data and `notes.csv` are intentionally ignored by Git
* statement that overlays are not yet implemented

Do not claim clinical or diagnostic validation.

## Privacy and repository safety

Medical imaging data and physician review data must remain local.

Never:

* remove `/data/` from `.gitignore`
* commit NIfTI participant files
* commit `notes.csv`
* use `git add -f` for ignored medical/review data
* create fake participant NIfTI data
* copy participant data from either reference repository
* upload medical data
* add analytics or telemetry
* make external API calls from the viewer
* add cloud storage
* expose the server outside localhost
* claim diagnostic or clinical validation

Do not log unnecessary participant metadata.

Displaying the participant ID inside the local viewer is expected functionality.

## Scope discipline

Prefer the smallest change that correctly adapts the working reference viewer.

Do not perform unrelated refactors.

Do not replace working code merely for stylistic consistency.

Do not introduce configuration frameworks.

Do not introduce environment variables for the data path.

Do not introduce databases.

Do not introduce a package manager.

Do not modify `niivue.umd.js`.

Do not modify the sibling repositories.

## Required validation

After implementation, run:

```bash
python -m py_compile server.py
```

Confirm that private files are not tracked:

```bash
git ls-files data notes.csv
```

This command must produce no output.

Check for inherited application terminology in implementation files:

```bash
git grep -n -E "Centiloid|Cohort_Centiloids|PET_MNI|PET_Space|VOI Controls|MNI template" -- server.py viewer.html README.md Start_Viewer.bat Start_Viewer.sh Start_Viewer.command
```

Any result must be reviewed and removed unless it is intentionally documenting migration history.

Do not generate fake NIfTI images merely to make automated testing pass.

With real local de-identified/authorized test data, manually verify at minimum:

* participant discovery
* natural participant ordering
* T1 loads
* T2 loads
* FLAIR loads
* missing modality disables only that modality
* modality switching
* Previous/Next
* Go to ID
* Go to index
* Navigate tool
* Zoom independently in axial/coronal/sagittal panes
* Reset Zoom independently by pane
* crosshair show/hide
* responsive resize
* Min/Max editing
* Window slider
* Window numeric input
* Level slider
* Level numeric input
* Window/Level and Min/Max remain mathematically synchronized
* Auto restores the image default range
* changing T1 intensity does not change T2/FLAIR intensity state
* notes locally autosave
* notes save to `notes.csv`
* saved reads reload
* launcher opens the VASC viewer
* no atlas, PET, MNI, VOI, or Centiloid controls remain

## Completion report

When the requested implementation is complete, report concisely:

1. files changed, created, or removed
2. major inherited behaviors preserved
3. major PET/MNI behaviors removed
4. subject/modality discovery behavior
5. validation commands run and their results
6. anything that could not be tested without real NIfTI data
7. any assumptions made

Do not claim that functionality was tested against real participant images unless it actually was.
