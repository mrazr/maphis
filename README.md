# Arthropod Describer

## Outline
1. [Features](#features)
2. [Running](#running)
3. [Installation](#installation)
4. [User guide](#user-guide)
5. [Plugins HOWTO](#plugins-howto)


## Features
- [x] Interactive tools
    - [x] Brush
    - [x] Knife
    - [x] Bucket
- [ ] Plugin system
  - [x] Region computations - plugin features that compute regions
  - [ ] Property computations - plugin features that compute properties of regions
    - deadline - Jan 4 2022
  - [ ] Tools - plugin specific tools
    - deadline - TBD

## Installation
**Note**: This setup was tested on Ubuntu 20.04, Windows has not been tested yet.

1. Clone this repository
2. Go to the root directory of the cloned repository
3. Create a new python virtual environment by running `python3 -m venv venv`
4. Activate the virtual environment: `source venv/bin/activate`
5. Install the requirements: `python3 -m pip install -r requirements.txt`
6. Install the app: `python3 -m pip install -e .`

## Running

1. In the repo's root directory activate the venv: `source venv/bin/activate`
2. Run: `python3 arthropod_describer/app.py`
3. When done, `deactivate` the venv, if you want.

## User guide

1. Import a folder with photos by clicking `File -> Open folder`.
   - The app will restructure the folder as follows:
   - 4 folders will be created:
     - `images`: all the images from the opened folder will be moved here.
     - `masks`: binary images marking bugs.
     - `sections`: integer label images marking sections of bug bodies
     - `reflections`: binary images marking reflection spots on bugs
   - **NOTE: as the app modifies the folder structure, may be it's better to work with a copy of the data.**
2. On the left a photo can be selected to view and modify its label images.
3. At top of photo view, active label image can be selected: `Bug`, `Segments`, `Reflections`
   - `Bug` serves as a mask for `Segments` and `Reflections`
4. On the right, a *colormap* can be selected; for a selected *colormap* the active *label* can be selected.
   - The selected label will be used by *tools*, which can be selected below the colormap selection widget.
5. On the `Plugin` tab you can browse the installed plugins and the computations that they provide.

### TODO - Saving
- Currently the label images are saved to disk when the user changes switches to another photo. This should be discussed, 
as in the old ArthDescriber version, the label images had to be explicitly "Approved" to be saved.

## Plugins HOWTO
This implementation of Arthropod Describer is essentially just a viewer for photos and their label images with three interactive tools; 
the main functionality comes from **plugins**.

### Plugin location
Plugins (each in its own separate directory) must be placed into `{root}/arthropod_describer/plugins/` .

### Plugin directory structure
An example of plugin directory structure:

```
.
├── __init__.py
├── plugin.py
├── properties
│   ├── __init__.py
│   └── average_intensity.py
├── tools
│   ├── __init__.py
│   └── some_cool_tool.py
├── plugin.py
└── regions
    ├── __init__.py
    ├── body.py
    ├── eraser.py
    └── legs.py
```

### Plugin code structure
A plugin consists of `RegionComputation`s, `PropertyComputation`s and `Tool`s.

`RegionComputation`s must be placed in `regions` dir, and similarly for `PropertyComputation`s and `Tool`s

### Creating a new plugin

To create a plugin, follow the above example directory structure, placed into the directory `plugins/`
Plugin is essentially just a aggregation of `Computation`s and `Tool`s, so start with creating them first.

#### Computation info
You must provide a name and description for every `Computation` that your plugin provides.
You do that by providing a class **docstring** in the required format.
Example:

```python
class BodyComp(RegionComputation):
  """
  NAME: Primitive bug body finder.
  DESC: Labels the whole body of a bug based on thresholding the blue channel.
  """
```

For computation that require some sort of user input, you can provide the user the option to tweak parameters.
Again, you define the user parameters in the **docstring**:

```python
class BodyComp(RegionComputation):
  """
  NAME: Primitive bug body finder.
  DESC: Labels the whole body of a bug based on thresholding the blue channel.

  USER_PARAMS:
      NAME: Blue threshold
      KEY: threshold
      PARAM_TYPE: INT
      VALUE: 200
      DEFAULT_VALUE: 200
      MIN_VALUE: 0
      MAX_VALUE: 255

      NAME: Filter size for small components
      KEY: filter_size
      PARAM_TYPE: INT
      VALUE: 25
      DEFAULT_VALUE: 25
      MIN_VALUE: 1
      MAX_VALUE: 55
  """
```

Each parameter's `KEY` must be unique within the `Computation`.

- `NAME` - this will be displayed in the App
- `KEY` - for internal identification, must be unique within the defining `Computation`
- `PARAM_TYPE` must be from `{INT, STR, BOOL}`
- `VALUE` - current value
- `DEFAULT_VALUE` - self-explanatory
- `MIN_VALUE`, `MAX_VALUE` - used only when `PARAM_TYPE`: INT, also self-explanatory


`Computation`s that can operate on individual regions, they can be declared as  `REGION_RESTRICTED`, as follows:

```python
class RegionEraser(RegionComputation):
  """
  NAME: Region eraser
  DESC: Erases regions with the selected labels.

  REGION_RESTRICTED
  """
```

Basically, put `REGION_RESTRICTED` anywhere in the **docstring**.
When the user will activate a `REGION_RESTRICTED` Computation, besides the Computation's user parameters, the user will be
also provided the option to select individual region labels on which the Computation will operate.

#### Region computation
Subclass the class `RegionComputation` located in the `arthropod_describer.common.plugin` module