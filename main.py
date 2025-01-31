import time
import requests
import tempfile
from morphcloud.api import MorphCloudClient

# Connect to the MorphCloud API
# The API key can be set through the client or as an environment variable MORPH_API_KEY
client = MorphCloudClient()

# Create a snapshot with 1 vCPU, 128MB memory, 700MB disk size, and the image "morphvm-minimal"
snapshot = client.snapshots.create(vcpus=1, memory=128, disk_size=700, image_id="morphvm-minimal")

# Start an instance from the snapshot and open an SSH connection
with client.instances.start(snapshot_id=snapshot.id) as instance, instance.ssh() as ssh:
    # Install uv and python using the ssh connection
    ssh.run(["curl -LsSf https://astral.sh/uv/install.sh | sh"]).raise_on_error()
    ssh.run(["echo 'source $HOME/.local/bin/env' >> $HOME/.bashrc"]).raise_on_error()
    ssh.run(["uv", "python", "install"]).raise_on_error()

    # Create an index.html file locally and copy it to the instance
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.writelines("<h1>Hello, World!</h1>")
        f.flush()
        ssh.copy_to(f.name, "index.html")

    # Start an HTTP server on the instance with a tunnel to the local machine and run it in the background
    with ssh.run(["uv", "run", "python3", "-m", "http.server", "8080", "--bind", "127.0.0.1"], background=True) as http_server, \
         ssh.tunnel(local_port=8888, remote_port=8080) as tunnel:

        # Wait for the HTTP server to start
        time.sleep(1)

        print("HTTP Server:", http_server.stdout)

        print("Making HTTP request")
        response = requests.get("http://127.0.0.1:8888", timeout=10)
        print("HTTP Response:", response.status_code)
        print(response.text)
