# Overview

The data clients for ROSE will be build upon lessons learned from
SmartRedis to create a library with embeddable clients that can be used
to transfer data to/from a compiled application. From experience, the
hybrid AI/HPC workflows that involve AI-in-the-Loop can be effectively
managed using producer/consumer architectures whose workflow processes
are driven by data availability. This document highlights the new
architecture which separates the behaviours of the client from the
implementation.

## Design Constraints

- Supports C++, Fortran, and C with the goal of feature parity between
  all three languages

- Support n-dimensional tensors across standard data types (especially
  float32 and float64)

- Assume that the user applications will be distributed programs

- User-facing APIs are separate from the implementation (e.g. DragonHPC
  vs. Redis)

- Basic put/get functionality can be achieved without ROSE

- Software stack does not rely on licenses which limit packaging

# SmartRedis Retrospective

SmartRedis relied on the RedisAI's use of dlpack to store tensor-like
data within the Redis in-memory, key-value store. This section reviews
key aspects of the SmartRedis architectures and makes recommendations to
retain, modify, or remove certain aspects

## Configuration via environment variables

**Recommendation: Retain**

Environment variables remain one of the most portable and performant
ways to send the necessary configuration options (e.g. database
address). To avoid bloating the environment, both the number of
variables and the content of the variables should be kept to a minimum.

## Data containers with metadata

**Recommendation: Retain**

The Dataset object allowed for multiple tensors to be sent as part of
the same payload (reducing the total amount of roundtrips) while also
being a natural way to infuse add metadata. ROSE may want to be
opinionated and create Dataset objects that have mandatory fields to aid
in rebuilding distributed datasets and/or to aid data discovery.

## Put/Get Semantics

**Recommendation: Modify**

The simplicity of put/get semantics lowers the barrier to entry for
application developers while also being the main behaviour needed to
connect simulations to a broader hybrid HPC/AI ecosystem. The following
asynchronous behaviours however should be added to improve performance
and simplify the architecture:

- Asynchronous puts: particularly for applications where there is no
  feedback into the simulation

- Futures-based approach to gets: enables latency-hiding behavior

- Blocking gets: required for workflows where retrieval of data is
  needed for the application to continue

## Run semantics

**Recommendation: Eliminate**

RedisAI allowed the functionality to execute TorchScript and Torch,
Tensorflow, and ONNX models using tensors that were already stored in
the database. This gives the application the ability to signal the
workflow and thus blurs the boundary of responsibilities between the
workflow coordinator and application.

# ROSE Enhancements

## In-memory data transfer clients

The lightweight SmartRedis library that provides clients and data
objects proved to be an intuitive solution for users wanting to
transition applications to an in-memory data transfer context. In
particular, the following characteristics must be obeyed

- Lightweight with dependencies that can be retrieved and compiled

- Provides both static and dynamically linked libraries

- Simple semantics (initialize/put/get)

- Immutable after initialization

- Low footprint to integrate into application code

These clients will be expected to work in two types of contexts: those
driven by ROSE and those by a generic workflow tool. For generic
workflows, the initialization will only require the bare minimum
information needed to authenticate/connect to a datastore. For
ROSE-driven workflows, the initialization behavior will involve the
Client Manager (detailed below) and mutate the defaults of the client to
serve the needs of the workflow, e.g. to change how keys are
constructed, whether data is sent This advanced client must be purely
additive to the basic, generic client which suggests a simple class
hierarchy where the *AdvancedClient* inherits from the *BasicClient.*

The emphasis on simplicity on the application client side does move
complexity to other components of the architecture. While SmartRedis
simply used keys to avoid conflicts, relying on naming conventions
proved to be onerous and imprecise. Instead, application clients are
required to use a data container with metadata. The client itself will
inject its own client identifier, issued by the client manager, to this
data container to aid the data manager (below) in its responsibilities.

## Client Manager

A client registry enables a mediator type paradigm for ROSE where the
necessary information needed for the workflow can flow from ROSE down
into the clients (see following section on Application Clients). On
initialization, the Client will emit an identifier (TBD, but likely
something akin to an MPI rank, application name, etc.) along with
user-configurable metadata (as needed) to the ROSE Client Manager (RCM).
The RCM can then respond to the registration request with any
configuration options needed by the client (e.g. which data fields
should be sent, the ROSE identifier for the client, etc.).

This register/response behavior will only be required in cases where the
client is part of a ROSE-driven workflow. In line withthe description of
the clients above, a non-null response is allowed if and only if the
*BasicClient* is used (though it will still receive one) and similarly a
stateful response is allowed if and only if the *AdvancedClient* is
being used. Unallowed behaviors must raise an exception.

## Data descriptors and contracts

For the types of loosely-coupled, data-driven workflows that ROSE
enables, facilitating data discovery and validating data
production/consumption within the workflow are key concerns. The ROSE
data manager (above) is the single source of truth. Two types of data
descriptors exist: 1) a canonical descriptor defined within ROSE and 2)
a (potentially) shorter descriptor defined within the application. The
second data descriptor essentially serves to validate that the
application can provide the correct data; the data manager is
responsible for validating the two via a *DataDescriptorValidator*.
While both descriptors have metadata fields, the canonical ROSE
descriptor will also have a variety of keywords to provide
flexibility/rigidity when enforcing the data contracts within
components.

- *fail-if-missing (default: False)*: error out if the application does
  not provide the field

- *warn-if-missing (default: True):* issue a warning if the application
  does not provide the field

- *fail-if-mismatch (default: False):* the value of the metadata must
  match exactly

- *warn-if-mismatch (default: True):* issue a warning if the value does
  not match

These defaults can also be overridden when instantiating the
*DataDescriptorValidator*. For the actual validation, requirements that
span multiple fields can be set:

- *fail-if-extra (default: False):* error out if the application
  provides additional fields

- *warn-if-extra (default: True):* issue a warning if the application
  provides additional fields

The ROSE descriptor will also include additional attributes that govern
correct behavior within the workflow.

- *modification-policy:* Restricts the type of mutations to the dataset

  - *overwrite (default):* Data can be overwritten at any time

  - *append-only: A*llow the dataset to grow along the specified
    dimension

  - *fixed:* The data can only be posted once

- *append-axis (default: \[None, int\]):* Specifies the axis that the
  dataset can grow along

The fundamental assumption that the data are coming from distributed
programs also requires the definition of what constitutes a "complete"
dataset. For example, a single distributed simulation may comprise many
ranks and so a dataset which requires the full global state should only
be marked as "complete" if all ranks have reported in. Similarly, for
datasets with multiple sources and/or ensembles of simulations, it may
only be complete when all ranks from all sources and/or ensemble members
have posted their data. After registering the data descriptor with the
data manager, the returned handle can be used to add sources. This
handle can also be passed to entities so that they can be used to
observe the progress of the dataset. By default, if there are no
sources, the dataset is considered complete as soon as it is posted.

## Data Manager

The data manager has two key responsibilities: 1) to be a single source
of truth for all data that is available in the ecosystem and 2) organize
higher level collections of data. The key behaviours of this data
manager are to:

- Be event-based, so that components of the workflow can accomplish
  their tasks when the data are available, without needing to poll

- Have a more interactive interface to allow for data discovery via
  metadata queries

- Mark "completeness" of datasets as they are fulfilled, e.g.
  rank-level, application-level, ensemble-level

- Separate access to metadata and data to enable rapid querying

- Enforce data contracts within the workflow (see above)
