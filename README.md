
# SpotDLPlugin para Jellyfin

Este proyecto es el plugin SpotDLPlugin para Jellyfin.

Desarrollado en C# (.NET 8.0), compatible con la arquitectura de plugins de Jellyfin.


## Requisitos

- [Dotnet SDK 8.0](https://dotnet.microsoft.com/download)
- Editor recomendado: Visual Studio Code, Visual Studio Community Edition, Mono Develop


## Instalación rápida

Clona este repositorio y abre la carpeta en tu IDE favorito. Compila el proyecto con:

```powershell
dotnet build SpotDLPlugin/SpotDLPlugin.csproj
```

Para publicar el plugin:

```powershell
dotnet publish SpotDLPlugin/SpotDLPlugin.csproj
```


## Estructura

- `SpotDLPlugin/SpotDLPlugin.csproj`: Proyecto principal del plugin
- `SpotDLPlugin/Plugin.cs`: Clase principal del plugin
- `SpotDLPlugin/Configuration/PluginConfiguration.cs`: Configuración del plugin
- `SpotDLPlugin/Configuration/configPage.html`: Página de configuración web


## Personalización

El plugin ya está adaptado para SpotDL. Puedes modificar la configuración y funcionalidad en los archivos fuente según tus necesidades.


## Licencia

Este plugin está bajo GPLv3, igual que el template oficial de Jellyfin.


## Funcionalidad avanzada

Puedes implementar cualquier interfaz de Jellyfin para ampliar las capacidades del plugin. Consulta la documentación oficial para más detalles: https://docs.jellyfin.org/general/contributing/index.html

## 5. Create a Repository

- [See blog post](https://jellyfin.org/posts/plugin-updates/)

## 6. Set Up Debugging

Debugging can be set up by creating tasks which will be executed when running the plugin project. The specifics on setting up these tasks are not included as they may differ from IDE to IDE. The following list describes the general process:

- Compile the plugin in debug mode.
- Create the plugin directory if it doesn't exist.
- Copy the plugin into your server's plugin directory. The server will then execute it.
- Make sure to set the working directory of the program being debugged to the working directory of the Jellyfin Server.
- Start the server.

Some IDEs like Visual Studio Code may need the following compile flags to compile the plugin:

```shell
dotnet build Your-Plugin.sln /property:GenerateFullPaths=true /consoleloggerparameters:NoSummary
```

These flags generate the full paths for file names and **do not** generate a summary during the build process as this may lead to duplicate errors in the problem panel of your IDE.

### 6.a Set Up Debugging on Visual Studio

Visual Studio allows developers to connect to other processes and debug them, setting breakpoints and inspecting the variables of the program. We can set this up following this steps:
On this section we will explain how to set up our solution to enable debugging before the server starts.

1. Right-click on the solution, And click on Add -> Existing Project...
2. Locate Jellyfin executable in your installation folder and click on 'Open'. It is called `Jellyfin.exe`. Now The solution will have a new "Project" called Jellyfin. This is the executable, not the source code of Jellyfin.
3. Right-click on this new project and click on 'Set up as Startup Project'
4. Right-click on this new project and click on 'Properties'
5. Make sure that the 'Attach' parameter is set to 'No'

From now on, everytime you click on start from Visual Studio, it will start Jellyfin attached to the debugger!

The only thing left to do is to compile the project as it is specified a few lines above and you are done.

### 6.b Automate the Setup on Visual Studio Code

Visual Studio Code allows developers to automate the process of starting all necessary dependencies to start debugging the plugin. This guide assumes the reader is familiar with the [documentation on debugging in Visual Studio Code](https://code.visualstudio.com/docs/editor/debugging) and has read the documentation in this file. It is assumed that the Jellyfin Server has already been compiled once. However, should one desire to automatically compile the server before the start of the debugging session, this can be easily implemented, but is not further discussed here.

A full example, which aims to be portable may be found in this repo's `.vscode` folder.

This example expects you to clone `jellyfin`, `jellyfin-web` and `jellyfin-plugin-template` under the same parent directory, though you can customize this in `settings.json`

1. Create a `settings.json` file inside your `.vscode` folder, to specify common options specific to your local setup.
   ```jsonc
    {
        // jellyfinDir : The directory of the cloned jellyfin server project
        // This needs to be built once before it can be used
        "jellyfinDir"     : "${workspaceFolder}/../jellyfin/Jellyfin.Server",
        // jellyfinWebDir : The directory of the cloned jellyfin-web project
        // This needs to be built once before it can be used
        "jellyfinWebDir"  : "${workspaceFolder}/../jellyfin-web",
        // jellyfinDataDir : the root data directory for a running jellyfin instance
        // This is where jellyfin stores its configs, plugins, metadata etc
        // This is platform specific by default, but on Windows defaults to
        // ${env:LOCALAPPDATA}/jellyfin
        "jellyfinDataDir" : "${env:LOCALAPPDATA}/jellyfin",
        // The name of the plugin
        "pluginName" : "Jellyfin.Plugin.Template",
    }
   ```

1. To automate the launch process, create a new `launch.json` file for C# projects inside the `.vscode` folder. The example below shows only the relevant parts of the file. Adjustments to your specific setup and operating system may be required.

   ```jsonc
    {
        // Paths and plugin names are configured in settings.json
        "version": "0.2.0",
        "configurations": [
            {
                "type": "coreclr",
                "name": "Launch",
                "request": "launch",
                "preLaunchTask": "build-and-copy",
                "program": "${config:jellyfinDir}/bin/Debug/net8.0/jellyfin.dll",
                "args": [
                //"--nowebclient"
                "--webdir",
                "${config:jellyfinWebDir}/dist/"
                ],
                "cwd": "${config:jellyfinDir}",
            }
        ]
    }

   ```

   The `request` type is specified as `launch`, as this `launch.json` file will start the Jellyfin Server process. The `preLaunchTask` defines a task that will run before the Jellyfin Server starts. More on this later. It is important to set the `program` path to the Jellyin Server program and set the current working directory (`cwd`) to the working directory of the Jellyfin Server.
   The `args` option allows to specify arguments to be passed to the server, e.g. whether Jellyfin should start with the web-client or without it.

2. Create a `tasks.json` file inside your `.vscode` folder and specify a `build-and-copy` task that will run in `sequence` order. This tasks depends on multiple other tasks and all of those other tasks can be defined as simple `shell` tasks that run commands like the `cp` command to copy a file. The sequence to run those tasks in is given below. Please note that it might be necessary to adjust the examples for your specific setup and operating system.

   The full file is shown here - Specific sections will be discussed in depth
    ```jsonc
    {
        // Paths and plugin name are configured in settings.json
        "version": "2.0.0",
        "tasks": [
            {
            // A chain task - build the plugin, then copy it to your
            // jellyfin server's plugin directory
            "label": "build-and-copy",
            "dependsOrder": "sequence",
            "dependsOn": ["build", "make-plugin-dir", "copy-dll"]
            },
            {
            // Build the plugin
            "label": "build",
            "command": "dotnet",
            "type": "shell",
            "args": [
                "publish",
                "${workspaceFolder}/${config:pluginName}.sln",
                "/property:GenerateFullPaths=true",
                "/consoleloggerparameters:NoSummary"
            ],
            "group": "build",
            "presentation": {
                "reveal": "silent"
            },
            "problemMatcher": "$msCompile"
            },
            {
                // Ensure the plugin directory exists before trying to use it
                "label": "make-plugin-dir",
                "type": "shell",
                "command": "mkdir",
                "args": [
                "-Force",
                "-Path",
                "${config:jellyfinDataDir}/plugins/${config:pluginName}/"
                ]
            },
            {
                // Copy the plugin dll to the jellyfin plugin install path
                // This command copies every .dll from the build directory to the plugin dir
                // Usually, you probablly only need ${config:pluginName}.dll
                // But some plugins may bundle extra requirements
                "label": "copy-dll",
                "type": "shell",
                "command": "cp",
                "args": [
                "./${config:pluginName}/bin/Debug/net8.0/publish/*",
                "${config:jellyfinDataDir}/plugins/${config:pluginName}/"
                ]

            },
        ]
    }

    ```
    1.  The "build-and-copy" task which triggers all of the other tasks
    ```jsonc
        {
        // A chain task - build the plugin, then copy it to your
        // jellyfin server's plugin directory
        "label": "build-and-copy",
        "dependsOrder": "sequence",
        "dependsOn": ["build", "make-plugin-dir", "copy-dll"]
        },
    ```
    2.  A build task. This task builds the plugin without generating summary, but with full paths for file names enabled.

        ```jsonc
            {
            // Build the plugin
            "label": "build",
            "command": "dotnet",
            "type": "shell",
            "args": [
                "publish",
                "${workspaceFolder}/${config:pluginName}.sln",
                "/property:GenerateFullPaths=true",
                "/consoleloggerparameters:NoSummary"
            ],
            "group": "build",
            "presentation": {
                "reveal": "silent"
            },
            "problemMatcher": "$msCompile"
            },
        ```

    3.  A tasks which creates the necessary plugin directory and a sub-folder for the specific plugin. The plugin directory is located below the [data directory](https://jellyfin.org/docs/general/administration/configuration.html) of the Jellyfin Server. As an example, the following path can be used for the bookshelf plugin: `$HOME/.local/share/jellyfin/plugins/Bookshelf/`
        ```jsonc
            {
                // Ensure the plugin directory exists before trying to use it
                "label": "make-plugin-dir",
                "type": "shell",
                "command": "mkdir",
                "args": [
                "-Force",
                "-Path",
                "${config:jellyfinDataDir}/plugins/${config:pluginName}/"
                ]
            },
        ```

    4.  A tasks which copies the plugin dll which has been built in step 2.1. The file is copied into it's specific plugin directory within the server's plugin directory.

        ```jsonc
            {
                // Copy the plugin dll to the jellyfin plugin install path
                // This command copies every .dll from the build directory to the plugin dir
                // Usually, you probablly only need ${config:pluginName}.dll
                // But some plugins may bundle extra requirements
                "label": "copy-dll",
                "type": "shell",
                "command": "cp",
                "args": [
                "./${config:pluginName}/bin/Debug/net8.0/publish/*",
                "${config:jellyfinDataDir}/plugins/${config:pluginName}/"
                ]
            },
        ```

## Licensing

Licensing is a complex topic. This repository features a GPLv3 license template that can be used to provide a good default license for your plugin. You may alter this if you like, but if you do a permissive license must be chosen.

Due to how plugins in Jellyfin work, when your plugin is compiled into a binary, it will link against the various Jellyfin binary NuGet packages. These packages are licensed under the GPLv3. Thus, due to the nature and restrictions of the GPL, the binary plugin you get will also be licensed under the GPLv3.

If you accept the default GPLv3 license from this template, all will be good. However if you choose a different license, please keep this fact in mind, as it might not always be obvious that an, e.g. MIT-licensed plugin would become GPLv3 when compiled.

Please note that this also means making "proprietary", source-unavailable, or otherwise "hidden" plugins for public consumption is not permitted. To build a Jellyfin plugin for distribution to others, it must be under the GPLv3 or a permissive open-source license that can be linked against the GPLv3.
