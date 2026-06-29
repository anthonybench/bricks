# General
- run-job doesn't pass job parameters. If you ever need parameterized runs, run_now supports job_parameters / notebook_params; a --param k=v option is the natural extension.
- Optional --json output. Tabulate is great for humans, but a --json flag emitting structured rows would make the tool composable in pipelines. Cheap to add given everything already funnels through row lists.
- Secret value on the command line. write-secret <scope> <key> <value> ... puts the literal secret in shell history and the process list (ps). Consider reading it from stdin or an env var (e.g. value - means read stdin), and/or warning in the docs. This is the one place a leak actually matters.

# update-clusters
New command `update-clusters <profile_list>`  that goes across each workspace in `<profile_list>` and makes sure that an interactive general purpose cluster exists that is:
  - is named `bricks_personal_cluster_name` (read from sleepyconfig)
  - owned by your user exists
  - uses the cluster policy named `bricks_personal_cluster_policy` (read from sleepyconfig), name expected to exist, errors gracefully if not found
  - is pinned
  - is latest LTS databricks runtime version

If `bricks_personal_cluster_name` is found but not pinned, it will pin it.
If the cluster name is found but using an old version, it will unpin, teardown, and rebuild as latest LTS databricks runtime version.
