# Description

The example here is as an initial POC to show how data can be exchanged in-memory
between the "simulation" component and the other python-based components of the active
learning loop. The in-memory exchange is accomplished using the Dragon DDict along with
cross-language Serializable types. The C++ code is "parallelized" using MPI where each
rank takes the same query points and returns its estimate of the "true" function.
Because random noise (whose seed is based on the rank and world size) these values are
not unique.

# Quick build

Currently the Serializables are based on a development branch of DragonHPC, but assuming
the user has access to this, the only step would be to type `make` in this directory to
compile the C++ client.
