## DESCRIPTION

*g.extension.github* downloads and installs, removes or updates
extensions (addons) from the official [GRASS GIS Addons
repository](https://grass.osgeo.org/grass8/manuals/addons/). It uses
*g.extension*. If a commit hash is set as **reference** then the addon
downloads the extension from GitHub according to this hash and uses
*g.extension* to install it.

## EXAMPLES

### Download and install of a specific version of a GRASS extension

Download and install a specific version of *i.sentinel* (identified via
GitHub commit hash) into current GRASS GIS installation:

```sh
g.extension.github extension=i.sentinel -f reference=aff69a9a0dac8c68ccb877858675d84588b35bd2
```

## SEE ALSO

*[g.extension](https://grass.osgeo.org/grass-stable/manuals/g.extension.html)*

## AUTHOR

Anika Weinmann, [mundialis](https://www.mundialis.de/), Germany
