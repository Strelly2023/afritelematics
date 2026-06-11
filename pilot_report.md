# Pilot Evidence Run Report

- classification: REVIEWABLE_PILOT_EVIDENCE
- production_proof: false
- authority_source: observability_only
- pilot_run_id: controlled-session-001
- generated_at: 2026-06-07T07:43:32.211023+00:00

This report is reviewable pilot evidence derived from observability only.
It does not certify production readiness or create proof authority.

## Summary Metrics

- total_observations: `284`
- success_count: `284`
- failure_count: `0`
- success_rate: `1.0`
- average_duration_ms: `25.95`
- max_duration_ms: `137`
- evidence_types_seen: `["app_backgrounded", "app_resumed", "driver_location_event", "driver_shift_started", "gps_accuracy_event", "network_latency_event", "ride_accept_latency", "route_deviation_event", "speed_consistency_event"]`
- unique_driver_count: `3`
- unique_trace_count: `284`

## Evidence Observations

### Observation 1

- pilot_run_id: controlled-session-001
- traceId: b4898046ddda5695b87793f4d4c3965b
- driverId: driver-demo-001
- evidenceType: driver_shift_started
- status: 200
- durationMs: 48
- structuredError: null
- timestamp: 2026-06-07T07:38:11.113299+00:00

### Observation 2

- pilot_run_id: controlled-session-001
- traceId: 758aff0ae2751af55e362913a32ab468
- driverId: driver-demo-001
- evidenceType: network_latency_event
- status: 200
- durationMs: 7
- structuredError: null
- timestamp: 2026-06-07T07:38:14.113538+00:00

### Observation 3

- pilot_run_id: controlled-session-001
- traceId: 3cbc88399469de9947e479d5b45d194d
- driverId: unknown_driver
- evidenceType: network_latency_event
- status: 200
- durationMs: 7
- structuredError: null
- timestamp: 2026-06-07T07:38:14.171865+00:00

### Observation 4

- pilot_run_id: controlled-session-001
- traceId: dfe9739d47f7a2951ef00f929c7cbf0f
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 11
- structuredError: null
- timestamp: 2026-06-07T07:38:17.198252+00:00

### Observation 5

- pilot_run_id: controlled-session-001
- traceId: d620970486169886c23baa0837e6cbd4
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 13
- structuredError: null
- timestamp: 2026-06-07T07:38:17.442486+00:00

### Observation 6

- pilot_run_id: controlled-session-001
- traceId: 3515230f68df07ac576f595ce653f4c5
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:38:18.886954+00:00

### Observation 7

- pilot_run_id: controlled-session-001
- traceId: cb62d9a661a17bdad51f982cea770fe2
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 19
- structuredError: null
- timestamp: 2026-06-07T07:38:18.950090+00:00

### Observation 8

- pilot_run_id: controlled-session-001
- traceId: eb53ab301ddc2026bdac74deb210841a
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:38:24.094624+00:00

### Observation 9

- pilot_run_id: controlled-session-001
- traceId: e8fcdf3bc64b336c16ee27ddfe4ef3db
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:38:24.169276+00:00

### Observation 10

- pilot_run_id: controlled-session-001
- traceId: 51c000e5e0344d6f4d104d665158b8ef
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 12
- structuredError: null
- timestamp: 2026-06-07T07:38:25.317251+00:00

### Observation 11

- pilot_run_id: controlled-session-001
- traceId: 618e2b3c395ccbd1792cfd88845327af
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:38:25.383567+00:00

### Observation 12

- pilot_run_id: controlled-session-001
- traceId: 534d04c2ecd5886fdbdad758608d9ea5
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 9
- structuredError: null
- timestamp: 2026-06-07T07:38:25.555685+00:00

### Observation 13

- pilot_run_id: controlled-session-001
- traceId: e263c24a26acae7ea25ff3e5b668c28a
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:38:26.093243+00:00

### Observation 14

- pilot_run_id: controlled-session-001
- traceId: 4bbb7295d89ee82f42ba082fccd46eb8
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:38:31.361764+00:00

### Observation 15

- pilot_run_id: controlled-session-001
- traceId: df8a8fb395ea60725d7bc270ab9f383d
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:38:31.429446+00:00

### Observation 16

- pilot_run_id: controlled-session-001
- traceId: cecd7fb9ca208d68ed352d30ef7b5395
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 7
- structuredError: null
- timestamp: 2026-06-07T07:38:32.701486+00:00

### Observation 17

- pilot_run_id: controlled-session-001
- traceId: b017a549467896b6787d8d757dd88318
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 9
- structuredError: null
- timestamp: 2026-06-07T07:38:32.749137+00:00

### Observation 18

- pilot_run_id: controlled-session-001
- traceId: 3922a8ff28a9952dac30cec5366bf753
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 9
- structuredError: null
- timestamp: 2026-06-07T07:38:32.804373+00:00

### Observation 19

- pilot_run_id: controlled-session-001
- traceId: 1c6a3f15342b8fe68da010f2292ae6a9
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 17
- structuredError: null
- timestamp: 2026-06-07T07:38:32.952971+00:00

### Observation 20

- pilot_run_id: controlled-session-001
- traceId: 1028d52c957b98704d226809bde22509
- driverId: driver-demo-001
- evidenceType: ride_accept_latency
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:38:33.339345+00:00

### Observation 21

- pilot_run_id: controlled-session-001
- traceId: 19e8d30b8ba82e99331d6ab92c691cf4
- driverId: driver-demo-001
- evidenceType: network_latency_event
- status: 200
- durationMs: 19
- structuredError: null
- timestamp: 2026-06-07T07:38:33.436647+00:00

### Observation 22

- pilot_run_id: controlled-session-001
- traceId: 2a43b59c4d8e470b5808d146a0d168b3
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 19
- structuredError: null
- timestamp: 2026-06-07T07:38:38.157143+00:00

### Observation 23

- pilot_run_id: controlled-session-001
- traceId: 966b5a3e1550e18b55e76d02c2daf9eb
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:38:38.201083+00:00

### Observation 24

- pilot_run_id: controlled-session-001
- traceId: 9e6887000a68cfedf76cdfcff2233afd
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:38:39.458721+00:00

### Observation 25

- pilot_run_id: controlled-session-001
- traceId: 7f852c889b8ab4a9a8a65720dc9e74b6
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:38:39.520922+00:00

### Observation 26

- pilot_run_id: controlled-session-001
- traceId: 1bc42db64e475ceba6181b0c7ebe00cf
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:38:39.870258+00:00

### Observation 27

- pilot_run_id: controlled-session-001
- traceId: f7cbd38a2019c521b1ac6b22723d5696
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:38:39.943009+00:00

### Observation 28

- pilot_run_id: controlled-session-001
- traceId: 478949c1f688bbd279224e51539b9cf2
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 27
- structuredError: null
- timestamp: 2026-06-07T07:38:45.256350+00:00

### Observation 29

- pilot_run_id: controlled-session-001
- traceId: fff1c42de46ebbb7438988b2d750d20e
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 17
- structuredError: null
- timestamp: 2026-06-07T07:38:45.308907+00:00

### Observation 30

- pilot_run_id: controlled-session-001
- traceId: ab530d08ba35c3d12ca79102263682d3
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:38:46.557673+00:00

### Observation 31

- pilot_run_id: controlled-session-001
- traceId: cfe80c19ad5ce83d5839f2eda202916e
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 28
- structuredError: null
- timestamp: 2026-06-07T07:38:46.642182+00:00

### Observation 32

- pilot_run_id: controlled-session-001
- traceId: add988d1b20a9cd2314121fced57de2f
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:38:46.708077+00:00

### Observation 33

- pilot_run_id: controlled-session-001
- traceId: 7080b58acd877371acfd873498b2c4bf
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:38:46.764067+00:00

### Observation 34

- pilot_run_id: controlled-session-001
- traceId: e5f4fdd0334bee96f855736327eb5897
- driverId: driver-demo-001
- evidenceType: network_latency_event
- status: 200
- durationMs: 19
- structuredError: null
- timestamp: 2026-06-07T07:38:48.957298+00:00

### Observation 35

- pilot_run_id: controlled-session-001
- traceId: 21e254f7fb3337f346af3dbf77d54ae3
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:38:51.971437+00:00

### Observation 36

- pilot_run_id: controlled-session-001
- traceId: 9d541c7bafeca21287ddc4c73734fa71
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 7
- structuredError: null
- timestamp: 2026-06-07T07:38:52.119375+00:00

### Observation 37

- pilot_run_id: controlled-session-001
- traceId: d1541b4b1dc27f048450e3dc836bea7c
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 6
- structuredError: null
- timestamp: 2026-06-07T07:38:52.182293+00:00

### Observation 38

- pilot_run_id: controlled-session-001
- traceId: 48a3ac67870bc60b782a383df916e3aa
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 14
- structuredError: null
- timestamp: 2026-06-07T07:38:52.397370+00:00

### Observation 39

- pilot_run_id: controlled-session-001
- traceId: 3de55699fc8b74a356916ef1069ee9d5
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 15
- structuredError: null
- timestamp: 2026-06-07T07:38:52.476807+00:00

### Observation 40

- pilot_run_id: controlled-session-001
- traceId: d1ed5497cf02f8424e28be7fa40abee3
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 8
- structuredError: null
- timestamp: 2026-06-07T07:38:52.531365+00:00

### Observation 41

- pilot_run_id: controlled-session-001
- traceId: 9f77a681f5b1e9d8e6b703338d2a0425
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 19
- structuredError: null
- timestamp: 2026-06-07T07:38:57.708550+00:00

### Observation 42

- pilot_run_id: controlled-session-001
- traceId: e9f97322bdaa24f0c4061b2eb3c2bbd5
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 16
- structuredError: null
- timestamp: 2026-06-07T07:38:57.768972+00:00

### Observation 43

- pilot_run_id: controlled-session-001
- traceId: a0caa3f549d8d91d0297c80f09e92a22
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:38:57.888275+00:00

### Observation 44

- pilot_run_id: controlled-session-001
- traceId: 892b4f163fb9d3783b5ce891fe3688cf
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:38:58.681355+00:00

### Observation 45

- pilot_run_id: controlled-session-001
- traceId: f56905adbec36f0a9f325e12c7dfe345
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:38:58.742353+00:00

### Observation 46

- pilot_run_id: controlled-session-001
- traceId: 13d50c0ffd18fea07fdcdea42f98db96
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:38:58.809590+00:00

### Observation 47

- pilot_run_id: controlled-session-001
- traceId: 3cd8e698b49b7353a27acb4e2eea5cca
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:38:58.905631+00:00

### Observation 48

- pilot_run_id: controlled-session-001
- traceId: ff0b9660f0a8ac22c8571749b78b64e9
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 105
- structuredError: null
- timestamp: 2026-06-07T07:39:09.745289+00:00

### Observation 49

- pilot_run_id: controlled-session-001
- traceId: 23325ad54b3f4bb727e7b5a1c655b8f3
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 120
- structuredError: null
- timestamp: 2026-06-07T07:39:09.758392+00:00

### Observation 50

- pilot_run_id: controlled-session-001
- traceId: 602d46db58fe68bd3e31ccc7c159fad2
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 38
- structuredError: null
- timestamp: 2026-06-07T07:39:09.763320+00:00

### Observation 51

- pilot_run_id: controlled-session-001
- traceId: e20c971f15661cde4d3cb8167a2dd5df
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 15
- structuredError: null
- timestamp: 2026-06-07T07:39:10.777557+00:00

### Observation 52

- pilot_run_id: controlled-session-001
- traceId: 36cf999b294a723bc42bbad8a532e5e3
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 11
- structuredError: null
- timestamp: 2026-06-07T07:39:10.828326+00:00

### Observation 53

- pilot_run_id: controlled-session-001
- traceId: b98a4dd31b2cd6205de033c06c1ba858
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 40
- structuredError: null
- timestamp: 2026-06-07T07:39:11.078703+00:00

### Observation 54

- pilot_run_id: controlled-session-001
- traceId: ad2a8454f82eb027ea8884bf1eefa752
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:39:11.464775+00:00

### Observation 55

- pilot_run_id: controlled-session-001
- traceId: 6d2d719f5f2c842f6bad7c84fbed3f6d
- driverId: driver-demo-001
- evidenceType: network_latency_event
- status: 200
- durationMs: 11
- structuredError: null
- timestamp: 2026-06-07T07:39:12.767053+00:00

### Observation 56

- pilot_run_id: controlled-session-001
- traceId: 93477477c4a4eaaca3c1dfe788046ac8
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:39:16.765002+00:00

### Observation 57

- pilot_run_id: controlled-session-001
- traceId: 6d80f840b7360e8643b85aefbbc736e6
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:39:16.772259+00:00

### Observation 58

- pilot_run_id: controlled-session-001
- traceId: 0eb7f517ab2c935883a6d11be82b86fc
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:39:17.769828+00:00

### Observation 59

- pilot_run_id: controlled-session-001
- traceId: 161e6703a92a54c7462a94c51795bb17
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 15
- structuredError: null
- timestamp: 2026-06-07T07:39:17.826733+00:00

### Observation 60

- pilot_run_id: controlled-session-001
- traceId: 42f0198c467e1e0d4d504875fbd9b411
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 6
- structuredError: null
- timestamp: 2026-06-07T07:39:17.883168+00:00

### Observation 61

- pilot_run_id: controlled-session-001
- traceId: 5de4e0827b962b9c72407f2c6ebbcb22
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 10
- structuredError: null
- timestamp: 2026-06-07T07:39:18.037389+00:00

### Observation 62

- pilot_run_id: controlled-session-001
- traceId: 8e4524f307bf95671d667ad9d1f21b97
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:39:23.254215+00:00

### Observation 63

- pilot_run_id: controlled-session-001
- traceId: 5994d1f00e0b3924db3c09c4941197d1
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 16
- structuredError: null
- timestamp: 2026-06-07T07:39:23.280035+00:00

### Observation 64

- pilot_run_id: controlled-session-001
- traceId: 90f9d68952874cd85781be32726105f1
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 13
- structuredError: null
- timestamp: 2026-06-07T07:39:24.493006+00:00

### Observation 65

- pilot_run_id: controlled-session-001
- traceId: 3e3686375a35a583589ad007ebd6991a
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 15
- structuredError: null
- timestamp: 2026-06-07T07:39:24.548473+00:00

### Observation 66

- pilot_run_id: controlled-session-001
- traceId: b41405ac6b0a8d2adfe70510fba45674
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:39:25.191395+00:00

### Observation 67

- pilot_run_id: controlled-session-001
- traceId: 6f2470fd19a2515e313ef7b5db3a5973
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:39:25.423724+00:00

### Observation 68

- pilot_run_id: controlled-session-001
- traceId: 008a5408cc98af72e250cd3e34395326
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 13
- structuredError: null
- timestamp: 2026-06-07T07:39:30.653089+00:00

### Observation 69

- pilot_run_id: controlled-session-001
- traceId: e76d2f6ba6e8569ab9b644770256b78b
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 9
- structuredError: null
- timestamp: 2026-06-07T07:39:30.671751+00:00

### Observation 70

- pilot_run_id: controlled-session-001
- traceId: a64637d382460a41301240ac3671fb8a
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 47
- structuredError: null
- timestamp: 2026-06-07T07:39:31.971425+00:00

### Observation 71

- pilot_run_id: controlled-session-001
- traceId: e24c7d693ffbba9483bfe4ec02991b46
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 106
- structuredError: null
- timestamp: 2026-06-07T07:39:32.123445+00:00

### Observation 72

- pilot_run_id: controlled-session-001
- traceId: d14c5f8862724e13dae9679790632359
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 61
- structuredError: null
- timestamp: 2026-06-07T07:39:32.239006+00:00

### Observation 73

- pilot_run_id: controlled-session-001
- traceId: b1586431b15011b5886797ef27a861ec
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 95
- structuredError: null
- timestamp: 2026-06-07T07:39:32.411978+00:00

### Observation 74

- pilot_run_id: controlled-session-001
- traceId: 4a4fa2b907ec6de749699f49beb22113
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 33
- structuredError: null
- timestamp: 2026-06-07T07:39:37.653236+00:00

### Observation 75

- pilot_run_id: controlled-session-001
- traceId: 0f561cb61c0688fe3bb1ba2669e926a7
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 26
- structuredError: null
- timestamp: 2026-06-07T07:39:37.664821+00:00

### Observation 76

- pilot_run_id: controlled-session-001
- traceId: 790cfc917382797e6eb4baa960e9c66d
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:39:38.813903+00:00

### Observation 77

- pilot_run_id: controlled-session-001
- traceId: fa3bec73986ff1ddea6c4caf7273e167
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 26
- structuredError: null
- timestamp: 2026-06-07T07:39:38.992155+00:00

### Observation 78

- pilot_run_id: controlled-session-001
- traceId: e0f3c63edcd14ea39257c8943759cf7a
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 19
- structuredError: null
- timestamp: 2026-06-07T07:39:39.177829+00:00

### Observation 79

- pilot_run_id: controlled-session-001
- traceId: fcf644d55a6dba562e10e3908b976e9a
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 12
- structuredError: null
- timestamp: 2026-06-07T07:39:39.240285+00:00

### Observation 80

- pilot_run_id: controlled-session-001
- traceId: 62e61d8e3d3f6213648db83b949aa9c0
- driverId: D001
- evidenceType: network_latency_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:39:39.911948+00:00

### Observation 81

- pilot_run_id: controlled-session-001
- traceId: 49f94ea27c47a59d2e815cf9174f9b21
- driverId: unknown_driver
- evidenceType: network_latency_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:39:40.108003+00:00

### Observation 82

- pilot_run_id: controlled-session-001
- traceId: b473576ec54d4cfa2d77ce010226c86d
- driverId: unknown_driver
- evidenceType: network_latency_event
- status: 200
- durationMs: 26
- structuredError: null
- timestamp: 2026-06-07T07:39:40.138082+00:00

### Observation 83

- pilot_run_id: controlled-session-001
- traceId: b22ddf0315926764f8c67b4bbfb7cf15
- driverId: unknown_driver
- evidenceType: network_latency_event
- status: 200
- durationMs: 13
- structuredError: null
- timestamp: 2026-06-07T07:39:40.176103+00:00

### Observation 84

- pilot_run_id: controlled-session-001
- traceId: 9c8f4ee5aa6398865adc88544a3c8a93
- driverId: driver-demo-001
- evidenceType: network_latency_event
- status: 200
- durationMs: 15
- structuredError: null
- timestamp: 2026-06-07T07:39:43.172993+00:00

### Observation 85

- pilot_run_id: controlled-session-001
- traceId: 65e23e34adc8b186ab65d05ca3b453b0
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 16
- structuredError: null
- timestamp: 2026-06-07T07:39:44.494115+00:00

### Observation 86

- pilot_run_id: controlled-session-001
- traceId: 433c548e9cca7969d0c96838698d58e0
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 17
- structuredError: null
- timestamp: 2026-06-07T07:39:44.590201+00:00

### Observation 87

- pilot_run_id: controlled-session-001
- traceId: 39fa8d070f712bf068d818f094e6b55c
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 13
- structuredError: null
- timestamp: 2026-06-07T07:39:45.814619+00:00

### Observation 88

- pilot_run_id: controlled-session-001
- traceId: 6f8871f38d48977712fa06f4baf207be
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 15
- structuredError: null
- timestamp: 2026-06-07T07:39:45.904565+00:00

### Observation 89

- pilot_run_id: controlled-session-001
- traceId: f4d9ac4657f15186b856b898b1ab2aca
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 13
- structuredError: null
- timestamp: 2026-06-07T07:39:45.965605+00:00

### Observation 90

- pilot_run_id: controlled-session-001
- traceId: df0169ea136abdb0eefed164b6558fd6
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:39:46.038243+00:00

### Observation 91

- pilot_run_id: controlled-session-001
- traceId: be13a8bf0969a26c076b6c40e4886656
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:39:51.218578+00:00

### Observation 92

- pilot_run_id: controlled-session-001
- traceId: c358baa8349c442ae917bfe23abba10d
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:39:51.308736+00:00

### Observation 93

- pilot_run_id: controlled-session-001
- traceId: e2804bb1bfccc19b13aa75ab662362b4
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 108
- structuredError: null
- timestamp: 2026-06-07T07:39:52.748561+00:00

### Observation 94

- pilot_run_id: controlled-session-001
- traceId: c9249d98e2d8308b07fa922d3c28d0b4
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:39:52.916953+00:00

### Observation 95

- pilot_run_id: controlled-session-001
- traceId: 523cdc5c63f949f222cc1e6c50ee3485
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 26
- structuredError: null
- timestamp: 2026-06-07T07:39:53.132050+00:00

### Observation 96

- pilot_run_id: controlled-session-001
- traceId: c0380d2f645f7cfc84d4ec859c17fc0b
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:39:53.208192+00:00

### Observation 97

- pilot_run_id: controlled-session-001
- traceId: f37a2cf627825bc3d87a165ece798c2c
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 17
- structuredError: null
- timestamp: 2026-06-07T07:39:58.529039+00:00

### Observation 98

- pilot_run_id: controlled-session-001
- traceId: 262b8c21332fc1ea57149bd35f953f10
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:39:58.603841+00:00

### Observation 99

- pilot_run_id: controlled-session-001
- traceId: bce85dada9fc90adddedf878f7924e74
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:39:59.947485+00:00

### Observation 100

- pilot_run_id: controlled-session-001
- traceId: 9f73f909869db08d9a37f3c3dbf794d5
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 61
- structuredError: null
- timestamp: 2026-06-07T07:40:00.070448+00:00

### Observation 101

- pilot_run_id: controlled-session-001
- traceId: bd7b58470a68e4b4618ac58c8cb17633
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:40:00.148120+00:00

### Observation 102

- pilot_run_id: controlled-session-001
- traceId: 401a0686ee9355ec6739a5a42d5baaeb
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:40:00.212431+00:00

### Observation 103

- pilot_run_id: controlled-session-001
- traceId: afef20fb5ce75267ef3f341964fe16d7
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 33
- structuredError: null
- timestamp: 2026-06-07T07:40:05.409406+00:00

### Observation 104

- pilot_run_id: controlled-session-001
- traceId: 6def047cbfa6b5714722402ccfa52ec5
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 19
- structuredError: null
- timestamp: 2026-06-07T07:40:05.478116+00:00

### Observation 105

- pilot_run_id: controlled-session-001
- traceId: 423900f22f08ecd4989ade92767ff8b0
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:40:06.775817+00:00

### Observation 106

- pilot_run_id: controlled-session-001
- traceId: 740013c449f0ccbd6cefd265eba9fe78
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:40:06.853514+00:00

### Observation 107

- pilot_run_id: controlled-session-001
- traceId: bb3e464ce70d909bdeec1400859ee126
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:40:07.045342+00:00

### Observation 108

- pilot_run_id: controlled-session-001
- traceId: 1eec524313d6bf73b13067f7fbceb2da
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:40:07.289947+00:00

### Observation 109

- pilot_run_id: controlled-session-001
- traceId: 595c041b201444a926871c6e2f7a4dbd
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 29
- structuredError: null
- timestamp: 2026-06-07T07:40:12.546947+00:00

### Observation 110

- pilot_run_id: controlled-session-001
- traceId: c1796a1787b06275d257fc024d5179c7
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 26
- structuredError: null
- timestamp: 2026-06-07T07:40:12.557563+00:00

### Observation 111

- pilot_run_id: controlled-session-001
- traceId: 0fbb0376f08ec683a90a7fe7eb7d914f
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:40:13.731953+00:00

### Observation 112

- pilot_run_id: controlled-session-001
- traceId: 3236ed3c308eb578c6e167ed77ff2c85
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:40:13.796146+00:00

### Observation 113

- pilot_run_id: controlled-session-001
- traceId: b32b7e692e32c43f06c5623ea4cc55af
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:40:13.858698+00:00

### Observation 114

- pilot_run_id: controlled-session-001
- traceId: 589eef23298546759b49b89cff700a3b
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 17
- structuredError: null
- timestamp: 2026-06-07T07:40:13.915108+00:00

### Observation 115

- pilot_run_id: controlled-session-001
- traceId: 880271b4bbce00f768b25bb0d80a2cd7
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 11
- structuredError: null
- timestamp: 2026-06-07T07:40:19.099851+00:00

### Observation 116

- pilot_run_id: controlled-session-001
- traceId: b34d4920ae67cfb5b50b9b7de8015343
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:40:19.228241+00:00

### Observation 117

- pilot_run_id: controlled-session-001
- traceId: ed6a0080162ccd2b498019bad0e0d9ce
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 61
- structuredError: null
- timestamp: 2026-06-07T07:40:20.565703+00:00

### Observation 118

- pilot_run_id: controlled-session-001
- traceId: 7e641231cc54097e01c1eb3cc3a5a469
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:40:20.737668+00:00

### Observation 119

- pilot_run_id: controlled-session-001
- traceId: ee4d52b221ec4cc8541de6e598224e2f
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 31
- structuredError: null
- timestamp: 2026-06-07T07:40:20.943281+00:00

### Observation 120

- pilot_run_id: controlled-session-001
- traceId: d5b213cbb9f4ae9d0edf7ec5a1630af5
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 29
- structuredError: null
- timestamp: 2026-06-07T07:40:21.135899+00:00

### Observation 121

- pilot_run_id: controlled-session-001
- traceId: adcefe922defba7d99e729425c883d94
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:40:26.441470+00:00

### Observation 122

- pilot_run_id: controlled-session-001
- traceId: 0bd5ea7bfe7e3d911f4d2447a5afbabb
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 16
- structuredError: null
- timestamp: 2026-06-07T07:40:26.541420+00:00

### Observation 123

- pilot_run_id: controlled-session-001
- traceId: 972c8219d521bcd216efedcd66bd9fae
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 42
- structuredError: null
- timestamp: 2026-06-07T07:40:27.607627+00:00

### Observation 124

- pilot_run_id: controlled-session-001
- traceId: e3702f660faf8153a5f2657a41e2765d
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:40:27.745825+00:00

### Observation 125

- pilot_run_id: controlled-session-001
- traceId: 21296492a227ed9440f945a1011ba1e5
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 7
- structuredError: null
- timestamp: 2026-06-07T07:40:27.799175+00:00

### Observation 126

- pilot_run_id: controlled-session-001
- traceId: c3a60f940984626186ffa3a0674cba30
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 11
- structuredError: null
- timestamp: 2026-06-07T07:40:27.854183+00:00

### Observation 127

- pilot_run_id: controlled-session-001
- traceId: 8439102795f72d733616ac3da7217e99
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 27
- structuredError: null
- timestamp: 2026-06-07T07:40:33.045205+00:00

### Observation 128

- pilot_run_id: controlled-session-001
- traceId: fc2547fe908225b52399b009bb342fbd
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 27
- structuredError: null
- timestamp: 2026-06-07T07:40:33.091834+00:00

### Observation 129

- pilot_run_id: controlled-session-001
- traceId: 5439e0c5e52fb5675d35e6a27e1cf643
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:40:34.292447+00:00

### Observation 130

- pilot_run_id: controlled-session-001
- traceId: a19b8e5562d2ab2057d167ca8a95f00e
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:40:34.693750+00:00

### Observation 131

- pilot_run_id: controlled-session-001
- traceId: 68bc70b066686b73fd34039777adaeda
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 28
- structuredError: null
- timestamp: 2026-06-07T07:40:34.780226+00:00

### Observation 132

- pilot_run_id: controlled-session-001
- traceId: 632d2eb34ce62c1f1ae7bdc09e3b6d44
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 10
- structuredError: null
- timestamp: 2026-06-07T07:40:34.942251+00:00

### Observation 133

- pilot_run_id: controlled-session-001
- traceId: 46003bb1e7d15ee994f034feeb348f0a
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 17
- structuredError: null
- timestamp: 2026-06-07T07:40:40.121721+00:00

### Observation 134

- pilot_run_id: controlled-session-001
- traceId: 6779ca2937d2a9a11246ea1a186e8775
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 30
- structuredError: null
- timestamp: 2026-06-07T07:40:40.177717+00:00

### Observation 135

- pilot_run_id: controlled-session-001
- traceId: 7637164c32fc79788d04df798e4cec7a
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:40:41.475632+00:00

### Observation 136

- pilot_run_id: controlled-session-001
- traceId: 6e89b18e0191c71533c100432f681a3e
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 77
- structuredError: null
- timestamp: 2026-06-07T07:40:41.605844+00:00

### Observation 137

- pilot_run_id: controlled-session-001
- traceId: 5b628ce2060bb30c93d3ad93f0c62bf3
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 94
- structuredError: null
- timestamp: 2026-06-07T07:40:41.772700+00:00

### Observation 138

- pilot_run_id: controlled-session-001
- traceId: 933ec13d84fb8de51d09a7c9b2f3d887
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:40:41.972201+00:00

### Observation 139

- pilot_run_id: controlled-session-001
- traceId: d1931c452cd198e32fbf85916df601c8
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 37
- structuredError: null
- timestamp: 2026-06-07T07:40:47.202189+00:00

### Observation 140

- pilot_run_id: controlled-session-001
- traceId: 992a23ee5ebbe1548d36553c35c56494
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:40:47.229630+00:00

### Observation 141

- pilot_run_id: controlled-session-001
- traceId: 1020b800388732fce89199c7d010326b
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:40:48.395945+00:00

### Observation 142

- pilot_run_id: controlled-session-001
- traceId: a17ef71d3cb4a34af9d0836e95484d90
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 11
- structuredError: null
- timestamp: 2026-06-07T07:40:48.438605+00:00

### Observation 143

- pilot_run_id: controlled-session-001
- traceId: 064bac72f4b4f66023e5cb040aeb79a6
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:40:48.613035+00:00

### Observation 144

- pilot_run_id: controlled-session-001
- traceId: 2089b985c1e0531438caff06b97037d6
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 30
- structuredError: null
- timestamp: 2026-06-07T07:40:48.854368+00:00

### Observation 145

- pilot_run_id: controlled-session-001
- traceId: bdaa09a7a62d2ce77738e4d73e8492bd
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:40:54.076016+00:00

### Observation 146

- pilot_run_id: controlled-session-001
- traceId: 633052455e1e0612cb61cc9df94ec668
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:40:54.105258+00:00

### Observation 147

- pilot_run_id: controlled-session-001
- traceId: 7edf7b46b4f6701c519b7e4f4fecd015
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:40:55.273146+00:00

### Observation 148

- pilot_run_id: controlled-session-001
- traceId: 0fe9569e615d4ca9fc58e8d602eb60a9
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:40:55.343017+00:00

### Observation 149

- pilot_run_id: controlled-session-001
- traceId: 313c2a0c90c75c6a2bd1a9e8da1b2959
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:40:55.421471+00:00

### Observation 150

- pilot_run_id: controlled-session-001
- traceId: a1e498c3580ea93c7a7fc818b48d232a
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:40:55.567520+00:00

### Observation 151

- pilot_run_id: controlled-session-001
- traceId: b3a7db881d6de1eb1f34286a1d6a6abd
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 74
- structuredError: null
- timestamp: 2026-06-07T07:41:00.896405+00:00

### Observation 152

- pilot_run_id: controlled-session-001
- traceId: 051258997e776f6f2b7b72fc159d822c
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 137
- structuredError: null
- timestamp: 2026-06-07T07:41:00.951971+00:00

### Observation 153

- pilot_run_id: controlled-session-001
- traceId: e6915cb956711f5006796277e232f4c8
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 41
- structuredError: null
- timestamp: 2026-06-07T07:41:02.049315+00:00

### Observation 154

- pilot_run_id: controlled-session-001
- traceId: 1a8accaf27860b76afeb5773fe956a2b
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 35
- structuredError: null
- timestamp: 2026-06-07T07:41:02.203613+00:00

### Observation 155

- pilot_run_id: controlled-session-001
- traceId: b45f11d7b323b820626bceb5f7f68a66
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 31
- structuredError: null
- timestamp: 2026-06-07T07:41:02.418885+00:00

### Observation 156

- pilot_run_id: controlled-session-001
- traceId: 32aaac55ac3c9d428d6493bbbfe51905
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:41:02.497717+00:00

### Observation 157

- pilot_run_id: controlled-session-001
- traceId: c97bf753a5e189bef724b4ac3a7e74d0
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 122
- structuredError: null
- timestamp: 2026-06-07T07:41:08.032889+00:00

### Observation 158

- pilot_run_id: controlled-session-001
- traceId: fb9f63f1d3480455554de7bacc1e16ef
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 132
- structuredError: null
- timestamp: 2026-06-07T07:41:08.038602+00:00

### Observation 159

- pilot_run_id: controlled-session-001
- traceId: 891c6bbe8af5ee21745549ed700e7e7e
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:41:09.039211+00:00

### Observation 160

- pilot_run_id: controlled-session-001
- traceId: b294504ba4a751796d747461a26e9933
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 26
- structuredError: null
- timestamp: 2026-06-07T07:41:09.196494+00:00

### Observation 161

- pilot_run_id: controlled-session-001
- traceId: e2ed6116c8669cf229ffd5bbf74de752
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 30
- structuredError: null
- timestamp: 2026-06-07T07:41:09.274893+00:00

### Observation 162

- pilot_run_id: controlled-session-001
- traceId: c1c4db19a8296f425770c7c5146c4e26
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 27
- structuredError: null
- timestamp: 2026-06-07T07:41:09.355279+00:00

### Observation 163

- pilot_run_id: controlled-session-001
- traceId: de317a2a481c13683c888b658a1e047f
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 65
- structuredError: null
- timestamp: 2026-06-07T07:41:14.661648+00:00

### Observation 164

- pilot_run_id: controlled-session-001
- traceId: b2b0bb81703b05cc2c497504ab0c7735
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:41:14.689401+00:00

### Observation 165

- pilot_run_id: controlled-session-001
- traceId: 8872cda0671ae7f285db5de2be523e37
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 17
- structuredError: null
- timestamp: 2026-06-07T07:41:15.960060+00:00

### Observation 166

- pilot_run_id: controlled-session-001
- traceId: 8a35322dd0488e96f59ca7e050e7fa37
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 28
- structuredError: null
- timestamp: 2026-06-07T07:41:16.343621+00:00

### Observation 167

- pilot_run_id: controlled-session-001
- traceId: 4a855bc70fcce5dae0fb08d9ea10b88e
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 31
- structuredError: null
- timestamp: 2026-06-07T07:41:16.586871+00:00

### Observation 168

- pilot_run_id: controlled-session-001
- traceId: 2a9e99e39e17606c911c07eca89a6305
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 28
- structuredError: null
- timestamp: 2026-06-07T07:41:16.660672+00:00

### Observation 169

- pilot_run_id: controlled-session-001
- traceId: 90cf0b458e8f53ea05932356a7403835
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 34
- structuredError: null
- timestamp: 2026-06-07T07:41:22.027598+00:00

### Observation 170

- pilot_run_id: controlled-session-001
- traceId: 002fad44a2cb47deb44185812f2b1f59
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 27
- structuredError: null
- timestamp: 2026-06-07T07:41:22.045232+00:00

### Observation 171

- pilot_run_id: controlled-session-001
- traceId: c0ae868fccb59669dfa6247a9e0168f4
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 28
- structuredError: null
- timestamp: 2026-06-07T07:41:23.355836+00:00

### Observation 172

- pilot_run_id: controlled-session-001
- traceId: 8d18eceb41c9ae141c7b9b93f6bbd52b
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 26
- structuredError: null
- timestamp: 2026-06-07T07:41:23.439225+00:00

### Observation 173

- pilot_run_id: controlled-session-001
- traceId: fb4a7f239ac55cdb796119ce13e63d4f
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 37
- structuredError: null
- timestamp: 2026-06-07T07:41:23.543083+00:00

### Observation 174

- pilot_run_id: controlled-session-001
- traceId: 622681d77149aee8b71b5e8156f74f3f
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 12
- structuredError: null
- timestamp: 2026-06-07T07:41:23.604675+00:00

### Observation 175

- pilot_run_id: controlled-session-001
- traceId: a143258b1f482ebcfbf4e1d1eb524776
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:41:28.843668+00:00

### Observation 176

- pilot_run_id: controlled-session-001
- traceId: 3197a97281939309906fe427be161e14
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 28
- structuredError: null
- timestamp: 2026-06-07T07:41:28.859459+00:00

### Observation 177

- pilot_run_id: controlled-session-001
- traceId: 920c7003fa00740ff1799d2f77e77482
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 26
- structuredError: null
- timestamp: 2026-06-07T07:41:30.014335+00:00

### Observation 178

- pilot_run_id: controlled-session-001
- traceId: a0c0da37db3fa6237597ec1ddbc3c8b0
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:41:30.175053+00:00

### Observation 179

- pilot_run_id: controlled-session-001
- traceId: 683206ae8d66052494bc89c9c2c7d9d0
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:41:30.224058+00:00

### Observation 180

- pilot_run_id: controlled-session-001
- traceId: fba4e6f0acaf25121f92ab88fb36a5fa
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:41:30.422000+00:00

### Observation 181

- pilot_run_id: controlled-session-001
- traceId: d26692a83c8861d74795546921bc736e
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:41:35.627091+00:00

### Observation 182

- pilot_run_id: controlled-session-001
- traceId: 9234e275f259839893c3dca70c29ed7a
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 19
- structuredError: null
- timestamp: 2026-06-07T07:41:35.677417+00:00

### Observation 183

- pilot_run_id: controlled-session-001
- traceId: 6f6fba04f70a445181653618ccdcd26c
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:41:37.140510+00:00

### Observation 184

- pilot_run_id: controlled-session-001
- traceId: 326f1a30bea44c4d5c3d0614c691a5f9
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:41:37.213564+00:00

### Observation 185

- pilot_run_id: controlled-session-001
- traceId: dd41dcc91bfcbbe99318b974aa706763
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:41:37.287628+00:00

### Observation 186

- pilot_run_id: controlled-session-001
- traceId: 8a200fb1dc411e05f8af5413961ca19b
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:41:37.352313+00:00

### Observation 187

- pilot_run_id: controlled-session-001
- traceId: 0b370d007ba707b81d7fc921a4ccbb0f
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 41
- structuredError: null
- timestamp: 2026-06-07T07:41:42.804132+00:00

### Observation 188

- pilot_run_id: controlled-session-001
- traceId: 87160071e569505c2637f8fbf7855479
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 57
- structuredError: null
- timestamp: 2026-06-07T07:41:42.823743+00:00

### Observation 189

- pilot_run_id: controlled-session-001
- traceId: 091e94fbe2714fbf1c97f7874c54c1db
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 28
- structuredError: null
- timestamp: 2026-06-07T07:41:43.877391+00:00

### Observation 190

- pilot_run_id: controlled-session-001
- traceId: 73661bbe2aa70a9c8fca947477a01348
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:41:43.941783+00:00

### Observation 191

- pilot_run_id: controlled-session-001
- traceId: da8001115b423948ecc26ee244531132
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:41:44.127855+00:00

### Observation 192

- pilot_run_id: controlled-session-001
- traceId: c08efb9db9b842f8b57d01357abdf235
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:41:44.341178+00:00

### Observation 193

- pilot_run_id: controlled-session-001
- traceId: 88761edb020fa90538cd48e0b2fe42e0
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:41:49.538392+00:00

### Observation 194

- pilot_run_id: controlled-session-001
- traceId: fc212cab83887ff6c579ea804c883b99
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 19
- structuredError: null
- timestamp: 2026-06-07T07:41:49.595891+00:00

### Observation 195

- pilot_run_id: controlled-session-001
- traceId: ba2868c6f94dcd01a79f31360d6b40a3
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 15
- structuredError: null
- timestamp: 2026-06-07T07:41:50.872950+00:00

### Observation 196

- pilot_run_id: controlled-session-001
- traceId: c506f4c60b0bbe915adfa347bb941d33
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 16
- structuredError: null
- timestamp: 2026-06-07T07:41:50.943395+00:00

### Observation 197

- pilot_run_id: controlled-session-001
- traceId: b253daef82a96e32560c07407ae98aea
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:41:51.105059+00:00

### Observation 198

- pilot_run_id: controlled-session-001
- traceId: 664dd8c4494b52afb1765e00bb7d9b8c
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 35
- structuredError: null
- timestamp: 2026-06-07T07:41:51.188780+00:00

### Observation 199

- pilot_run_id: controlled-session-001
- traceId: 7ea5266d14eb8bff33f04c73d3c10346
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 26
- structuredError: null
- timestamp: 2026-06-07T07:41:56.397428+00:00

### Observation 200

- pilot_run_id: controlled-session-001
- traceId: 584afb265fb6579756fe32b3fb189d00
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:41:56.458578+00:00

### Observation 201

- pilot_run_id: controlled-session-001
- traceId: 4f94be5a4b0c6ed7bb7bd55282961d29
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 27
- structuredError: null
- timestamp: 2026-06-07T07:41:57.721533+00:00

### Observation 202

- pilot_run_id: controlled-session-001
- traceId: 12a16bbbabbc105235e737653eda54da
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 16
- structuredError: null
- timestamp: 2026-06-07T07:41:57.920481+00:00

### Observation 203

- pilot_run_id: controlled-session-001
- traceId: 817530781f3cad57b1857344f2e51608
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:41:57.991548+00:00

### Observation 204

- pilot_run_id: controlled-session-001
- traceId: e8a064a46ab87d0b300f186e3a2a7e88
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:41:58.208641+00:00

### Observation 205

- pilot_run_id: controlled-session-001
- traceId: d59046b3fcb0e0939770febd3f813b45
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 35
- structuredError: null
- timestamp: 2026-06-07T07:42:03.399610+00:00

### Observation 206

- pilot_run_id: controlled-session-001
- traceId: ee7305f45721bc80b600e482c2154508
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:42:03.456912+00:00

### Observation 207

- pilot_run_id: controlled-session-001
- traceId: 6041e44cb90ac1a49b940672a77da48f
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:42:04.760895+00:00

### Observation 208

- pilot_run_id: controlled-session-001
- traceId: fd94adba76a7884d0bd58f08623d13f3
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:42:04.830805+00:00

### Observation 209

- pilot_run_id: controlled-session-001
- traceId: 32ca44fa8ee899cfd3651fb2b4a38e49
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:42:04.896020+00:00

### Observation 210

- pilot_run_id: controlled-session-001
- traceId: 847f0f705e1661243bb72f7227e78af1
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 28
- structuredError: null
- timestamp: 2026-06-07T07:42:04.975563+00:00

### Observation 211

- pilot_run_id: controlled-session-001
- traceId: 7649cbbfa272e8b63676e71ea0987092
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 29
- structuredError: null
- timestamp: 2026-06-07T07:42:10.156098+00:00

### Observation 212

- pilot_run_id: controlled-session-001
- traceId: abe87137d93e95721db8f833019444ae
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 40
- structuredError: null
- timestamp: 2026-06-07T07:42:10.254108+00:00

### Observation 213

- pilot_run_id: controlled-session-001
- traceId: 9d6f69bce45379a85145db8b909fc313
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 12
- structuredError: null
- timestamp: 2026-06-07T07:42:11.596935+00:00

### Observation 214

- pilot_run_id: controlled-session-001
- traceId: ae27c0bef03bf58b8906575a2daee4a7
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 27
- structuredError: null
- timestamp: 2026-06-07T07:42:11.793816+00:00

### Observation 215

- pilot_run_id: controlled-session-001
- traceId: 63ed18b6897c57c64245f8e79e8b61ae
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 31
- structuredError: null
- timestamp: 2026-06-07T07:42:12.075311+00:00

### Observation 216

- pilot_run_id: controlled-session-001
- traceId: d77625bc647cdf29ac16667e35c8207c
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 15
- structuredError: null
- timestamp: 2026-06-07T07:42:12.445875+00:00

### Observation 217

- pilot_run_id: controlled-session-001
- traceId: 3439aa83288ab1b90e0ac2965514f9a7
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 39
- structuredError: null
- timestamp: 2026-06-07T07:42:17.681882+00:00

### Observation 218

- pilot_run_id: controlled-session-001
- traceId: 96602b8ca641e73334bb834c343d1a23
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 33
- structuredError: null
- timestamp: 2026-06-07T07:42:17.699289+00:00

### Observation 219

- pilot_run_id: controlled-session-001
- traceId: 6d3936e5f782a71f82d7d5f990de6ced
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:42:18.710524+00:00

### Observation 220

- pilot_run_id: controlled-session-001
- traceId: be9a61265a280f6f60b9b6436abc1264
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:42:18.779961+00:00

### Observation 221

- pilot_run_id: controlled-session-001
- traceId: 08dade27080226dca128cc2b4a2082cf
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 32
- structuredError: null
- timestamp: 2026-06-07T07:42:18.947392+00:00

### Observation 222

- pilot_run_id: controlled-session-001
- traceId: 1dc1e006d18d1dab99be0626ea4d3bce
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 118
- structuredError: null
- timestamp: 2026-06-07T07:42:19.126177+00:00

### Observation 223

- pilot_run_id: controlled-session-001
- traceId: e1a1514687700518d68f15e8a0aa82bb
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 16
- structuredError: null
- timestamp: 2026-06-07T07:42:24.348988+00:00

### Observation 224

- pilot_run_id: controlled-session-001
- traceId: 25b902c7a1ea4da4905b08b080d09dec
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 16
- structuredError: null
- timestamp: 2026-06-07T07:42:24.414089+00:00

### Observation 225

- pilot_run_id: controlled-session-001
- traceId: 7a2f334804023b0f6841016f35789016
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:42:25.567536+00:00

### Observation 226

- pilot_run_id: controlled-session-001
- traceId: 8ba863088743cb7f4d1bbf224adf48a7
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 17
- structuredError: null
- timestamp: 2026-06-07T07:42:25.779934+00:00

### Observation 227

- pilot_run_id: controlled-session-001
- traceId: af70f64b4c777adc2820eb30f96f6235
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 16
- structuredError: null
- timestamp: 2026-06-07T07:42:25.838481+00:00

### Observation 228

- pilot_run_id: controlled-session-001
- traceId: 70c2fd14a35829ae245911247ed762db
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:42:26.020308+00:00

### Observation 229

- pilot_run_id: controlled-session-001
- traceId: d4920fbb820f1814258df284084ddff0
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 30
- structuredError: null
- timestamp: 2026-06-07T07:42:31.241940+00:00

### Observation 230

- pilot_run_id: controlled-session-001
- traceId: fb23fe214fd3675e24ac938a2b2f3ad8
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 19
- structuredError: null
- timestamp: 2026-06-07T07:42:31.288990+00:00

### Observation 231

- pilot_run_id: controlled-session-001
- traceId: d54084d74f0d1f8f7e4c5e40962a0d48
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 17
- structuredError: null
- timestamp: 2026-06-07T07:42:32.558507+00:00

### Observation 232

- pilot_run_id: controlled-session-001
- traceId: 8808ad4c5d007c5bd8f73a9684ff31c5
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 10
- structuredError: null
- timestamp: 2026-06-07T07:42:32.613471+00:00

### Observation 233

- pilot_run_id: controlled-session-001
- traceId: 1bc3bf39c30ac018e5d7674c38fbb815
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 33
- structuredError: null
- timestamp: 2026-06-07T07:42:32.690793+00:00

### Observation 234

- pilot_run_id: controlled-session-001
- traceId: 93f2d26fb7453d949abc291e2eb68394
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:42:32.755725+00:00

### Observation 235

- pilot_run_id: controlled-session-001
- traceId: 1ef31eb45bf1284e677ec1343c9bd34a
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:42:37.944238+00:00

### Observation 236

- pilot_run_id: controlled-session-001
- traceId: 807363a46980e2e5eeb0165a07dd085a
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:42:38.029782+00:00

### Observation 237

- pilot_run_id: controlled-session-001
- traceId: 1ad7427fd261a2da4a46c389e448ec22
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:42:39.194567+00:00

### Observation 238

- pilot_run_id: controlled-session-001
- traceId: 375ceea9c2118f55457263425a64b047
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:42:39.397239+00:00

### Observation 239

- pilot_run_id: controlled-session-001
- traceId: 71d92e3fcf5c3a463eccf30bbb0de557
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:42:39.469147+00:00

### Observation 240

- pilot_run_id: controlled-session-001
- traceId: 9262ab52a64107b9f00c05e95774d0eb
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:42:39.659148+00:00

### Observation 241

- pilot_run_id: controlled-session-001
- traceId: 8f3e661730f8e29ecc4235204f3e7d27
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 28
- structuredError: null
- timestamp: 2026-06-07T07:42:44.864682+00:00

### Observation 242

- pilot_run_id: controlled-session-001
- traceId: 26eadd46b558ce2f35a6f431a4c72a2a
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:42:44.921689+00:00

### Observation 243

- pilot_run_id: controlled-session-001
- traceId: 051ef562565a264275c5687efedef2f1
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 12
- structuredError: null
- timestamp: 2026-06-07T07:42:46.194846+00:00

### Observation 244

- pilot_run_id: controlled-session-001
- traceId: 6583f65a37ea52a7a39a3489955941c7
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:42:46.363728+00:00

### Observation 245

- pilot_run_id: controlled-session-001
- traceId: 2f3ea1c4b3ca69e72e93cdff9eca0dae
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 15
- structuredError: null
- timestamp: 2026-06-07T07:42:46.427618+00:00

### Observation 246

- pilot_run_id: controlled-session-001
- traceId: 5d6193a33d78a9217eeeb1b18cc10335
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 17
- structuredError: null
- timestamp: 2026-06-07T07:42:46.489322+00:00

### Observation 247

- pilot_run_id: controlled-session-001
- traceId: c2ab8877e6fc124fa188dfb892ff45c2
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 15
- structuredError: null
- timestamp: 2026-06-07T07:42:51.688308+00:00

### Observation 248

- pilot_run_id: controlled-session-001
- traceId: 414236c0751159f8b1e2e8a584a8415a
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 19
- structuredError: null
- timestamp: 2026-06-07T07:42:51.716635+00:00

### Observation 249

- pilot_run_id: controlled-session-001
- traceId: 9dc930c8455efead1b872fecc54c86e8
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:42:52.991614+00:00

### Observation 250

- pilot_run_id: controlled-session-001
- traceId: c5c1485b4d979a57bf1fe7aefd85b014
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 15
- structuredError: null
- timestamp: 2026-06-07T07:42:53.183674+00:00

### Observation 251

- pilot_run_id: controlled-session-001
- traceId: c469f1074e07464d8fe5290ebddbf2f6
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:42:53.246825+00:00

### Observation 252

- pilot_run_id: controlled-session-001
- traceId: 3f048de122cc847fe7006f1605d324c4
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:42:53.497961+00:00

### Observation 253

- pilot_run_id: controlled-session-001
- traceId: eb288ede98cd641a19981558fe7ce235
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 38
- structuredError: null
- timestamp: 2026-06-07T07:42:58.845577+00:00

### Observation 254

- pilot_run_id: controlled-session-001
- traceId: bd19278c8b7c6bea7896ca73c96bfa6a
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:42:58.893676+00:00

### Observation 255

- pilot_run_id: controlled-session-001
- traceId: f3cdb6753419c0135cc6a5471dbd19e4
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 54
- structuredError: null
- timestamp: 2026-06-07T07:43:00.095227+00:00

### Observation 256

- pilot_run_id: controlled-session-001
- traceId: 7495b80ba2f96d814375d6445cddb64b
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 19
- structuredError: null
- timestamp: 2026-06-07T07:43:00.209259+00:00

### Observation 257

- pilot_run_id: controlled-session-001
- traceId: 5eddb10cdc04b7344a25de9989e18232
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 25
- structuredError: null
- timestamp: 2026-06-07T07:43:00.354664+00:00

### Observation 258

- pilot_run_id: controlled-session-001
- traceId: c61c187d35b1496734fe82e98742f0eb
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 14
- structuredError: null
- timestamp: 2026-06-07T07:43:00.410713+00:00

### Observation 259

- pilot_run_id: controlled-session-001
- traceId: 22fc9281e5d2fb7c53384dc8b8df117a
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:43:05.610819+00:00

### Observation 260

- pilot_run_id: controlled-session-001
- traceId: 777a884db5ea688607f25061d786ba1d
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 14
- structuredError: null
- timestamp: 2026-06-07T07:43:05.681659+00:00

### Observation 261

- pilot_run_id: controlled-session-001
- traceId: 2643e7ddc0e05536f3e7583c06a69446
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 26
- structuredError: null
- timestamp: 2026-06-07T07:43:07.002228+00:00

### Observation 262

- pilot_run_id: controlled-session-001
- traceId: d62c98db9fd4e9d938db9ac8d43b78ff
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 12
- structuredError: null
- timestamp: 2026-06-07T07:43:07.225980+00:00

### Observation 263

- pilot_run_id: controlled-session-001
- traceId: d77dc3603e94a507ef0a3bd74b3de0d7
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:43:07.294842+00:00

### Observation 264

- pilot_run_id: controlled-session-001
- traceId: f32767ec27d443463d1ebdbfe374ff87
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:43:07.467738+00:00

### Observation 265

- pilot_run_id: controlled-session-001
- traceId: f205ad60d3b33d26f5fbc72e01df3d9a
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 45
- structuredError: null
- timestamp: 2026-06-07T07:43:12.731768+00:00

### Observation 266

- pilot_run_id: controlled-session-001
- traceId: a51f53f0b843e3155ecbb14f4d9eace7
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 33
- structuredError: null
- timestamp: 2026-06-07T07:43:12.755627+00:00

### Observation 267

- pilot_run_id: controlled-session-001
- traceId: de7f2f4e0a946f8c3b02580ec21d3a71
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 24
- structuredError: null
- timestamp: 2026-06-07T07:43:14.008214+00:00

### Observation 268

- pilot_run_id: controlled-session-001
- traceId: 7188bce6af9150850a0b9c2ad18a6970
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:43:14.077808+00:00

### Observation 269

- pilot_run_id: controlled-session-001
- traceId: 619059d297378c44332620bae04271b9
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:43:14.160723+00:00

### Observation 270

- pilot_run_id: controlled-session-001
- traceId: bd14269699177ffa6d90de6245031e0f
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 18
- structuredError: null
- timestamp: 2026-06-07T07:43:14.231653+00:00

### Observation 271

- pilot_run_id: controlled-session-001
- traceId: a78e92bc21fd2dd6b01cae5792c19745
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 13
- structuredError: null
- timestamp: 2026-06-07T07:43:19.407131+00:00

### Observation 272

- pilot_run_id: controlled-session-001
- traceId: 87c9b0aa3b2c7b2bcc8fa1c6484488e7
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 14
- structuredError: null
- timestamp: 2026-06-07T07:43:19.511515+00:00

### Observation 273

- pilot_run_id: controlled-session-001
- traceId: 9a3172085d8754e4c6c6a83332435455
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 31
- structuredError: null
- timestamp: 2026-06-07T07:43:20.769021+00:00

### Observation 274

- pilot_run_id: controlled-session-001
- traceId: 2b35fe36dc465098549286e6d864c7ab
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 14
- structuredError: null
- timestamp: 2026-06-07T07:43:20.826055+00:00

### Observation 275

- pilot_run_id: controlled-session-001
- traceId: c5b22be5835a9166a50d21d4c18f9172
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 12
- structuredError: null
- timestamp: 2026-06-07T07:43:20.926161+00:00

### Observation 276

- pilot_run_id: controlled-session-001
- traceId: f810d39b8d645d4545362fed176ac652
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 10
- structuredError: null
- timestamp: 2026-06-07T07:43:20.981987+00:00

### Observation 277

- pilot_run_id: controlled-session-001
- traceId: 4765ab6ddddc630a042d489b0a11ea36
- driverId: driver-demo-001
- evidenceType: app_backgrounded
- status: 200
- durationMs: 21
- structuredError: null
- timestamp: 2026-06-07T07:43:26.189465+00:00

### Observation 278

- pilot_run_id: controlled-session-001
- traceId: 0b3d767a5731d7483595854a2d9e3c8c
- driverId: driver-demo-001
- evidenceType: app_resumed
- status: 200
- durationMs: 20
- structuredError: null
- timestamp: 2026-06-07T07:43:26.322922+00:00

### Observation 279

- pilot_run_id: controlled-session-001
- traceId: 31267ab1b62d0b77c2915e119edbb09e
- driverId: driver-demo-001
- evidenceType: driver_location_event
- status: 200
- durationMs: 23
- structuredError: null
- timestamp: 2026-06-07T07:43:27.442342+00:00

### Observation 280

- pilot_run_id: controlled-session-001
- traceId: 53c0f2f99c4d7aab104cf9f128793091
- driverId: driver-demo-001
- evidenceType: gps_accuracy_event
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:43:27.576717+00:00

### Observation 281

- pilot_run_id: controlled-session-001
- traceId: f3d118296985ae484a26033af6cb0be4
- driverId: driver-demo-001
- evidenceType: speed_consistency_event
- status: 200
- durationMs: 19
- structuredError: null
- timestamp: 2026-06-07T07:43:27.625651+00:00

### Observation 282

- pilot_run_id: controlled-session-001
- traceId: e24a59a2e74a2f7d90aeb20081a76d67
- driverId: driver-demo-001
- evidenceType: route_deviation_event
- status: 200
- durationMs: 22
- structuredError: null
- timestamp: 2026-06-07T07:43:27.685900+00:00

### Observation 283

- pilot_run_id: controlled-session-001
- traceId: a38534868d769e24866f4d5adfdaf57d
- driverId: driver-demo-001
- evidenceType: network_latency_event
- status: 200
- durationMs: 15
- structuredError: null
- timestamp: 2026-06-07T07:43:28.698327+00:00

### Observation 284

- pilot_run_id: controlled-session-001
- traceId: 3e2f719152e6c172cbce0b92f1804e68
- driverId: unknown_driver
- evidenceType: network_latency_event
- status: 200
- durationMs: 10
- structuredError: null
- timestamp: 2026-06-07T07:43:28.741146+00:00
