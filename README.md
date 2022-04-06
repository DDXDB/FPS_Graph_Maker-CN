# FPS_Graph_Maker
Creates animated graphs from different FPS CSV files.
Currently only works with Elgato's 4k Capture Utility's logging feature.

# Installation & Requirements
Requires Python 3.4 or newer.
Install the dependencies using the install_dependencies.bat for Windows,
or alternatively run the following command:
```
pip install -r requirements.txt
```
or:
```
python -m pip install -r requirements.txt
```

If you use the `pipenv` module, you can create a virtual environment with the
following command:
```
pipenv update
```
or:
```
python -m pipenv update
```

# Usage
You can use the help command to get a list of available options with the
following command:
```
python fps_2_chart.py -h
```

Here is what that output looks like:
```
usage: fps_2_chart.py [-h] [-o OUTPUT] [--fps] [--frametime] [--combined] [-r {720p,1080p,1440p,4k}] [-d DPI] [-w]
                      CSV_Report

Plot CSV report to to a live video graph.

positional arguments:
  CSV_Report      FPS CSV report file.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output filename (Default: "graph").
                        Depending on what you generate, the output files will have "_fps" or "_frametime" or "_both" appended to them
                        (IE: "graph" would generate "graph_fps.mov").
  --fps
                        Output a live FPS graph file.
  --frametime
                        Output a live Frametime graph file.
  --combined
                        Output a combined live FPS + Frametime graph file.
  -r {720p,1080p,1440p,4k}, --resolution {720p,1080p,1440p,4k}
                        Choose the resolution for the graph video (Default is 1080p).
                        Note that higher values will mean drastically larger files and take substantially longer to encode.
  -d DPI, --dpi DPI     Choose the DPI value for the graph image and video (Default is 100).
                        The DPI value must be greater than or equal to 2.
                        Note that higher values will mean drastically larger files and take substantially longer to encode.
```

# Contributing
Any commits that look to improve this application is appreciated! The main focus pints / TO-DO for this app (inn order of highest to lowest priority) is as follows:
1. Frame interpolation & downsampling
  - Not all apps log their information at a constant rate (IE: one measure per millisecond)
  - This variable logging rate means that placing data pointso n a live graph that expects conistent spacing is an issue
  - The goal would be to interpolate the data to get rid of the gaps
  - This causes a new issue of having more frame to encode, requiring either a faster framerate