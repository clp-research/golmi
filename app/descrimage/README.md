# Pentomino Experiment

This experiment has a UI which renders a Penomino board with pento pieces and a gripper.
The gripper can be navigated with the cursors and can drag or drop pieces using SPACE.

The pentomino experiment shows the basic expected structure of an experiment. 
You can copy, rename and adjust this folder for your needs.

```
pentomino
    +- static     
    |    +- css            (your custom CSS files to be loaded in your main html file)
    |       +- pentomino.css
    |    +- js             (your main JS files to be loaded in your main html file)
    |       +- pentomino.js
    |    +- resources      (additional resources you may need to load)
    |           +- config
    |               +- pentomino_config.json (the main config for your experiments)
    +- templates
        +- pentomino.html (your main html file)
```

You can reference your static files in your html using the following syntax:

```
<script src="{{ url_for('pentomino_bp.static', filename='js/pentomino.js') }}"></script>
```

If you want to reference sources from Golmi use the following syntax:

```
<script src="{{ url_for('static', filename='js/controller/LocalKeyController.js') }}"></script>
```
