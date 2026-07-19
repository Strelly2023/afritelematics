# NovaRide rollback plan

- Keep the current branch and evidence artifacts immutable unless a later authorized deployment changes them.
- Do not remove volumes, secrets, or user data.
- Use the existing deployment evidence as the rollback reference point.
