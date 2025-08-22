import subprocess

sln_path = "Jellyfin.Plugin.Template.sln"  # Cambia el nombre si tu .sln es diferente
configuration = "Debug"

def publish_solution(sln_path, configuration="Debug"):
    cmd = [
        "dotnet", "publish",
        "--configuration", configuration,
        sln_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("Error al publicar la solución:")
        print(result.stderr)
    else:
        print("Publicación exitosa.")

if __name__ == "__main__":
    publish_solution(sln_path, configuration)
