# AfriRide Pilot Deployment Architecture

ADR-0041 defines the governed pilot deployment manifest for live operations.

## Boundary

- Pilot deployment references the production spine.
- Pilot deployment is read-only and reference-only.
- Pilot deployment does not redefine runtime truth.

