# Solution Engineering Deployment Guide

Build the portal with the existing Vite pipeline:

```bash
cd novacodepro_portal
npm ci
npm run build
```

The production Docker build copies the portal source, installs dependencies,
and serves the built assets under `/novacodepro/`.

Recommended verification:

- portal root returns `200`
- login route returns `200`
- `/novacodepro/solutions` returns the SPA shell
- `/novacodepro/solutions/projects/:projectId` returns the project shell
- API routes for Solution Engineering and Workflow Fabric are present in OpenAPI
