# OpenShell local boundary probe

This local test exercised **OpenShell 0.1.2** on macOS arm64 with Docker Desktop Engine 29.7.2. A temporary Docker gateway used local mTLS for CLI calls and sandbox JWT authentication for supervisor callbacks. The gateway was bound to loopback and had access to the Docker socket while it ran. The sandbox ran a tiny image containing only two public fixture strings from `openshell-image/`. No host workspace, home directory, `.env`, provider credentials, or private plant files were mounted or attached. The sandbox, gateway, Docker volume, local certificate bundle, and fixture image were removed after testing.

The effective policy from `openshell-policy.yaml` loaded at revision 1, hash `7a4234391c16b227072795bc893b04d0b7db6c7763f40ebbe6a9dcd00aa98e04`. It granted read-only access to `/work/allowed`, omitted `/work/denied`, and had no network rules. The sandbox was `Ready`. The saved [probe trace](openshell-trace.json) records an allowed file read, denied read, denied write, and denied direct TCP connection; the allowed fixture remained unchanged afterward. These are observed local sandbox controls for this test image and policy, not a claim about a deployed plant workflow or private-data protection.

To repeat after setting up an authenticated local gateway with the [official container deployment guide](https://docs.nvidia.com/openshell/latest/how-it-works/gateways/container-deployment), build the fixture and run:

```sh
docker build -t openshell-hackathon-fixture:local integrations/openshell-image
openshell sandbox create --name hack-public --from openshell-hackathon-fixture:local --policy integrations/openshell-policy.yaml --no-auto-providers --detach
openshell policy get hack-public --full
openshell policy list hack-public
openshell sandbox exec -n hack-public --no-login-shell -- cat /work/allowed/fixture.txt
openshell sandbox exec -n hack-public --no-login-shell -- cat /work/denied/fixture.txt
openshell sandbox exec -n hack-public --no-login-shell -- bash -c 'echo changed > /work/allowed/fixture.txt'
openshell sandbox exec -n hack-public --no-login-shell -- timeout 5 bash -c 'echo probe > /dev/tcp/1.1.1.1/443'
openshell sandbox delete hack-public
```

The OpenShell CLI and supervisor binary came from NVIDIA's `v0.1.2` GitHub release and passed the published SHA-256 checksums. OpenShell's [policy reference](https://docs.nvidia.com/openshell/latest/how-it-works/policies/schema) documents `hard_requirement` Landlock and default-deny network behavior. A first plaintext gateway attempt could not create a Docker sandbox because this version requires launch-scoped gateway authentication. An initial authenticated attempt with host port 18080 could not connect the sandbox supervisor; mapping port 8080 to 8080 resolved it. The final test used the authenticated gateway and exact port mapping.
