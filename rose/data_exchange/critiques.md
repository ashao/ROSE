## Draft 1: comments
- Q: What do you mean by "Immutable after initialization"? What is immutable?
- A: The client configuration is immutable after initialization. This is to prevent the behaviour of the client to evolve without the knowledge of the client manager

- Q: Backend components and lifecycle
- A: The backend components will be managed by ROSE as part of the primary workflow execution. Open question: can these be threads on the main workflow process or should we spawn these as separate process potentially on different nodes?

- Q: User app data interactions
- A: Primary app data interaction is the following:
1. ROSE-level: Provides the "canonical" data description for datasets expected to be produced/consumed within the workflow
2. App: On initialization, applications register their own data descriptors with incoming/outgoing intention
3. ROSE data manager: validates the descriptors and issues a handle for the application
4. App: Application uses the handle to put/get the data

- Q: other dependencies or actors that tap into the data (really asking about any potential synchronizations)
- A: For the main ROSE workflow process, the registration of the canonical descriptor returns a handle that can be used to determine completeness and/or monitor progress of the completion of the dataset (or in the case of datasets which are constantly appended to, the number of 'records' in that dataset). This can be useful to avoid deploying components of the workflow that do not need to even execute until a data criteria exists. An event publication stream that notifies subscribers on dataset modifications at various levels of granularity may also need to tap into the data handles

- Q: more on the behaviors of the descriptors and contracts
- A: This might be easier to describe in code rather than in text, however briefly the application specifies a descriptor and a policy that determines how strict the validation of the app-provided descriptor to the canonical one there needs to be. The contract from the point of view of the ROSE backend components is mainly "application will provide" and from the side of the application "application can provide". The ROSE backend validates that anyone requesting the data has an application that can provide the data.

- Q: How dataset completeness works across multiple ranks or sources
- A: The number of sources expected to comprise a "record" (a complete slice) of the dataset is part of the canonical descriptor. From multiple sources, this can be a collection of individual data sources. Completeness is calculated based on the hierarchy of completeness from its constituents

- Q: What happens if one of the ranks fails.How is recovery handled — or is that out of scope?
- A: For MPI-distributed components, this may rely on MPI-native recovery methodologies (e.g. duplication of ranks). If a component fails, but has checkpoints/restarts, does ROSE provide capability to automatically restart the application? If so, then multiple registrations are allowed, so long as the descriptors match. For datasets with 'records', part of the required put should include the record-identifier. The overwrite policy on the canonical data descriptor will control whether the information will be rewritten or is read-only after the initial post.

- Q: Since ROSE workflows run asynchronously, blocking operations could be a serious issue. Are we planning to provide an async API? This is pretty critical for ROSE
- A: This primarily depends on the application itself. For the "get" operations we can make them asynchronous by returning a future of some variety, for the "put" operations those can trivially be done async. For "get" operations, blocking operations would likely take the form of a return with a timeout. Most of the data exchange happens under the hood between applications. ROSE is not intended to be a semaphore manager for the internal execution of the application itself.